"""
scraper.py — Scrape TikTok profile dengan data lengkap.

Pendekatan:
  1. CDP inject interceptor SEBELUM navigasi (tangkap semua API request)
  2. Scroll untuk load video
  3. Ambil urutan dari DOM (pinned video tetap pertama)
  4. Gabung data API + DOM
"""

import os
import json
import time
import io
import logging
import traceback
import urllib.request
from datetime import datetime

from PIL import Image

from .driver import create_driver

logger = logging.getLogger(__name__)

TIKTOK_BASE_URL = "https://www.tiktok.com/@"
STALL_LIMIT = 8

# JavaScript: ambil urutan video ID dari DOM
JS_GET_ID_ORDER = """
var items = document.querySelectorAll('a[href*="/video/"]');
var ids = [];
var seen = {};
items.forEach(function(a) {
    var m = (a.getAttribute('href')||'').match(/\\/video\\/(\\d+)/);
    if (m && !seen[m[1]]) { seen[m[1]] = true; ids.push(m[1]); }
});
return JSON.stringify(ids);
"""

# JavaScript: baca data dari interceptor
JS_GET_DATA = "return JSON.stringify(window.__tt || []);"


class TikTokScraper:
    """
    Scraper untuk profile TikTok dengan data lengkap.

    Args:
        username: Username TikTok (tanpa @)
        max_videos: Jumlah maksimal video (0 = semua)
        output_file: True=simpan file JSON/TXT/CSV, False=tidak (default False)
        profile_path: Path ke folder Chromium profile (opsional)
        output_dir: Folder untuk output file (opsional)

    Usage:
        # Basic - tanpa file output (programmatic)
        scraper = TikTokScraper("salehot0", max_videos=20)
        videos = scraper.run()

        # Dengan file output
        scraper = TikTokScraper("salehot0", max_videos=20, output_file=True)
        videos = scraper.run()

        # Hasil:
        for v in videos:
            print(v["id"], v["views"], v["upload_date"], v["desc"][:30])
    """

    def __init__(self, username, max_videos=0, output_file=False, profile_path=None, output_dir=None):
        self.username = username
        self.max_videos = max_videos if max_videos > 0 else 999999
        self.output_file = output_file
        self.profile_path = profile_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "chromium"
        )
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp"
        )

        self.videos = []
        self._api = {}
        self._dom_order = []
        self._driver = None
        self._stalled = 0

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def run(self):
        """
        Jalankan scraping.

        Returns:
            list[dict]: Daftar video dengan data lengkap.
                        Contoh: [{"id","desc","views","likes","upload_date",...}, ...]
        """
        driver = self._create_driver()
        if not driver:
            return []
        self._driver = driver

        try:
            url = f"{TIKTOK_BASE_URL}{self.username}"
            logger.info("Membuka: %s", url)

            # Inject interceptor SEBELUM navigasi (via CDP)
            self._inject_interceptor(driver)

            # Navigasi
            driver.get(url)
            time.sleep(10)

            # Scroll
            logger.info("Scrolling...")
            self._scroll_until_done()
            time.sleep(2)

            # Collect data
            self._collect_api()
            self._capture_dom_order()

            # Merge & output
            logger.info("Gabung data...")
            self._merge()

            # Download thumbnails
            logger.info("Download thumbnails...")
            self._download_thumbnails()

            self._display()
            if self.output_file:
                self._save()

            return self.videos

        except Exception as e:
            logger.error("Error: %s", e)
            traceback.print_exc()
            return []
        finally:
            logger.info("Tutup browser...")
            try:
                driver.quit()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # INTERNAL
    # ------------------------------------------------------------------

    def _inject_interceptor(self, driver):
        """Inject fetch interceptor via CDP (sebelum navigasi)."""
        logger.info("Inject interceptor via CDP...")
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    window.__tt = [];
                    var f = window.fetch.bind(window);
                    window.fetch = function(url, init) {
                        var s = (typeof url == 'string') ? url : (url&&url.url?url.url:'');
                        return f(url, init).then(function(r) {
                            r.clone().text().then(function(t) {
                                if (s.includes('/api/post/item_list')) {
                                    try { window.__tt.push(JSON.parse(t)); } catch(e) {}
                                }
                            }).catch(function(){});
                            return r;
                        });
                    };
                """
            })
        except Exception as e:
            logger.warning("CDP inject gagal: %s", e)
            # Fallback: inject setelah load
            driver.get(f"{TIKTOK_BASE_URL}{self.username}")
            time.sleep(5)
            driver.execute_script("""
                window.__tt = [];
                var f = window.fetch.bind(window);
                window.fetch = function(url, init) {
                    var s = (typeof url == 'string') ? url : (url&&url.url?url.url:'');
                    return f(url, init).then(function(r) {
                        r.clone().text().then(function(t) {
                            if (s.includes('/api/post/item_list')) {
                                try { window.__tt.push(JSON.parse(t)); } catch(e) {}
                            }
                        }).catch(function(){});
                        return r;
                    });
                };
            """)

    def _create_driver(self):
        path = os.path.abspath(self.profile_path)
        if not os.path.isdir(path):
            logger.error("Folder profile tidak ditemukan: %s", path)
            return None
        try:
            return create_driver(profile_path=path)
        except Exception as e:
            logger.error("Gagal buat driver: %s", e)
            return None

    def _count_links(self):
        try:
            return self._driver.execute_script(
                "return document.querySelectorAll('a[href*=\"/video/\"]').length;"
            )
        except Exception:
            return 0

    def _scroll_until_done(self):
        max_scrolls = min(500, self.max_videos * 2 + 5) if self.max_videos != 999999 else 500
        min_scrolls = min(3, max_scrolls)

        for i in range(max_scrolls):
            link_count = self._count_links()
            if i >= min_scrolls and link_count >= self.max_videos:
                logger.info("Target %d video tercapai (links=%d).", self.max_videos, link_count)
                return
            if self._stalled >= STALL_LIMIT:
                return

            self._driver.execute_script("window.scrollBy(0, window.innerHeight*0.8);")
            time.sleep(2.0)
            new_count = self._count_links()
            self._stalled = 0 if new_count > link_count else self._stalled + 1

            pct = f"{min(100, new_count * 100 // self.max_videos)}%" if self.max_videos != 999999 else f"{new_count}v"
            logger.info("Scroll #%d | links=%d | %s | stalled=%d", i + 1, new_count, pct, self._stalled)

    def _collect_api(self):
        """Baca data dari JS interceptor."""
        try:
            raw = self._driver.execute_script(JS_GET_DATA)
            responses = json.loads(raw) if raw else []
        except Exception:
            responses = []

        if not responses:
            logger.info("Interceptor: tidak ada data API.")
            return

        parsed = 0
        for resp in responses:
            for item in resp.get("itemList", []) or resp.get("item_list", []):
                vid = str(item.get("id", ""))
                if not vid:
                    continue

                st = item.get("stats", {}) or {}
                st = st if isinstance(st, dict) else {}
                vi = item.get("video", {}) or {}
                vi = vi if isinstance(vi, dict) else {}
                au = item.get("author", {}) or {}
                au = au if isinstance(au, dict) else {}
                ct = item.get("createTime", 0) or 0

                ud = datetime.fromtimestamp(ct).strftime("%Y-%m-%d %H:%M:%S") if ct else ""
                thumbnail = vi.get("cover", "") or vi.get("dynamicCover", "") or vi.get("originCover", "") or ""

                self._api[vid] = {
                    "id": vid,
                    "desc": item.get("desc", "") or "",
                    "views": int(st.get("playCount", 0) or 0),
                    "likes": int(st.get("diggCount", 0) or 0),
                    "comments": int(st.get("commentCount", 0) or 0),
                    "shares": int(st.get("shareCount", 0) or 0),
                    "upload_date": ud,
                    "upload_timestamp": int(ct),
                    "duration_sec": int(vi.get("duration", 0) or 0),
                    "thumbnail_url": thumbnail,
                    "author": au.get("uniqueId", "") or au.get("nickname", "") or self.username,
                    "video_url": f"https://www.tiktok.com/@{self.username}/video/{vid}",
                }
                parsed += 1

        logger.info("Interceptor: %d video dari API (parsed %d).", len(self._api), parsed)

    def _capture_dom_order(self):
        """Ambil urutan video dari DOM (pastikan pinned tetap pertama)."""
        try:
            raw = self._driver.execute_script(JS_GET_ID_ORDER)
            self._dom_order = json.loads(raw) if raw else []
        except Exception:
            self._dom_order = []
        logger.info("DOM order: %d video.", len(self._dom_order))

    def _merge(self):
        """Gabung data API + DOM order."""
        self.videos = []
        for vid in self._dom_order:
            if vid in self._api:
                self.videos.append(self._api[vid])

        # Tambah video dari API yang tidak ada di DOM
        api_ids = set(self._api.keys())
        dom_ids = set(self._dom_order)
        for vid in api_ids - dom_ids:
            self.videos.append(self._api[vid])

        # Batasi
        if self.max_videos != 999999 and len(self.videos) > self.max_videos:
            self.videos = self.videos[:self.max_videos]

        wd = sum(1 for v in self.videos if v["desc"])
        wu = sum(1 for v in self.videos if v["upload_date"])
        logger.info("Merge: %d video (caption=%d date=%d)", len(self.videos), wd, wu)

    def _download_thumbnails(self):
        """
        Download dan cache thumbnail untuk setiap video.

        Thumbnail dianggap sebagai cache permanen — hanya didownload SATU KALI.
        Jika file thumbnail.jpg sudah ada, download dan resize dilewati.

        Lokasi penyimpanan:
            static/videos/<video_id>/thumbnail.jpg

        Ukuran:
            - tinggi maksimum 120 px
            - aspect ratio dipertahankan
            - simpan sebagai JPG kualitas 85
        """
        static_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "static"
        )

        for v in self.videos:
            vid = v.get("id", "")
            thumb_url = v.get("thumbnail_url", "")
            if not vid or not thumb_url:
                continue

            thumb_path = os.path.join(static_dir, "videos", vid, "thumbnail.jpg")

            # ==========================================================
            # OPTIMASI: Jika thumbnail sudah ada, skip download
            # Thumbnail video TikTok hampir tidak pernah berubah setelah
            # video dipublikasikan. Cukup download SATU KALI.
            # ==========================================================
            if os.path.exists(thumb_path):
                logger.debug("Thumbnail exists, skip: %s", thumb_path)
                continue

            # Buat folder
            thumb_dir = os.path.dirname(thumb_path)
            os.makedirs(thumb_dir, exist_ok=True)

            try:
                # Download
                req = urllib.request.Request(
                    thumb_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                                      "Chrome/120.0.0.0 Safari/537.36"
                    }
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    img_data = resp.read()

                # Resize dengan Pillow
                img = Image.open(io.BytesIO(img_data))
                w, h = img.size
                if h > 120:
                    ratio = 120.0 / h
                    new_w = int(w * ratio)
                    img = img.resize((new_w, 120), Image.LANCZOS)

                # Simpan sebagai JPG
                img.convert("RGB").save(thumb_path, "JPEG", quality=85, optimize=True)

                logger.debug("Thumbnail saved: %s", thumb_path)

            except Exception as e:
                logger.warning("Gagal download thumbnail %s: %s", vid, e)
                # Non-fatal: tetap lanjut ke video berikutnya

    def _display(self):
        """Tampilkan ringkasan ke console."""
        if not self.videos:
            logger.warning("Kosong.")
            return

        tv = sum(v["views"] for v in self.videos)
        tl = sum(v["likes"] for v in self.videos)

        print(f"\n{'=' * 80}")
        print(f"  HASIL @{self.username} | {len(self.videos)} video | Views: {tv:,}")
        if tl:
            print(f"  Likes: {tl:,}")
        print(f"{'=' * 80}")

        for i, v in enumerate(self.videos[:5], 1):
            d = f" | {v['upload_date']}" if v['upload_date'] else ""
            print(f"  [{i}] ID={v['id']} | Views={v['views']:,}{d}")
            cap = v['desc'][:80] if v['desc'] else "(no caption)"
            print(f"       {cap}")

        print(f"\n  Output: {self.output_dir}/\n")

    def _save(self):
        """Simpan ke JSON, TXT, CSV."""
        if not self.videos:
            return

        os.makedirs(self.output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"tiktok_{self.username}_{len(self.videos)}videos_{ts}"

        # JSON
        path = os.path.join(self.output_dir, f"{base}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "username": self.username,
                "total": len(self.videos),
                "scraped_at": datetime.now().isoformat(),
                "videos": self.videos,
            }, f, ensure_ascii=False, indent=2)

        # TXT
        path = os.path.join(self.output_dir, f"{base}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"TikTok @{self.username} - {len(self.videos)} videos\n")
            f.write(f"Scraped: {datetime.now().isoformat()}\n\n")
            for i, v in enumerate(self.videos, 1):
                f.write(
                    f"[{i:4d}] ID={v['id']}\n"
                    f" Views={v['views']:,} Likes={v['likes']:,} "
                    f"Comments={v['comments']:,} Shares={v['shares']:,}\n"
                    f" Upload={v['upload_date']} Duration={v['duration_sec']}s\n"
                    f" Caption={v['desc']}\n"
                    f" URL={v['video_url']}\n"
                    f" Thumb={v['thumbnail_url']}\n"
                    + "-" * 70 + "\n"
                )

        # CSV
        path = os.path.join(self.output_dir, f"{base}.csv")
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("No,VideoID,Views,Likes,Comments,Shares,UploadDate,DurationSec,Caption,VideoURL,ThumbnailURL\n")
            for i, v in enumerate(self.videos, 1):
                c = v['desc'].replace('"', '""').replace("\n", " ").replace("\r", "")
                f.write(
                    f'{i},{v["id"]},{v["views"]},{v["likes"]},'
                    f'{v["comments"]},{v["shares"]},{v["upload_date"]},'
                    f'{v["duration_sec"]},"{c}",{v["video_url"]},{v["thumbnail_url"]}\n'
                )

        logger.info("Saved JSON/TXT/CSV")
