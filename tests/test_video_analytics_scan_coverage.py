"""
Regression test untuk COVERAGE scan Video Analytics.

Konteks bug (creator_id = 2 / "Kang Petruk"):
    Database berisi 195 video, tetapi snapshot hari ini hanya ~91 video karena
    ada artificial cap pada alur scan:

        routers/creator/video_analytics.py   : max_videos = 90
        includes/tiktok_scrape_videos/scraper.py : self.videos = self.videos[:self.max_videos]
        includes/video_performance/scanner.py    : max_videos=max(20, scroll_count * 10)

Kontrak yang diuji (HARD LIMIT):
    - Scraper: maksimal MAX_VIDEOS (190) video UNIK & MAX_SCROLLS (8) scroll.
    - Berhenti SEGERA bila 190 video unik tercapai ATAU 8 scroll tercapai;
      tidak ada scroll ke-9.
    - max_videos=0 TIDAK lagi berarti unlimited (diperlakukan sebagai 190).
    - DB tidak menerima lebih dari MAX_VIDEOS (190) video dari satu collection.

Selain itu test ini membedakan metrik:
    fetched, filtered, processed, processed_success, processed_failed,
    snapshots_written.

File ini memakai fake scraper + fake DB writer (tanpa MySQL dan tanpa
seleniumbase). Modul `includes.tiktok_scrape_videos.driver` di-stub karena
butuh seleniumbase yang tidak tersedia di environment test.

Jalankan:
    python -m unittest tests.test_video_analytics_scan_coverage -v
"""

import importlib
import os
import sys
import types
import unittest
from unittest import mock

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------------------
# STUB dependency berat (seleniumbase) yang tidak tersedia di environment
# test. Harus dipasang SEBELUM import modul scraper.
# ------------------------------------------------------------------
if "includes.tiktok_scrape_videos.driver" not in sys.modules:
    _fake_driver_mod = types.ModuleType("includes.tiktok_scrape_videos.driver")
    _fake_driver_mod.create_driver = lambda *args, **kwargs: None
    sys.modules["includes.tiktok_scrape_videos.driver"] = _fake_driver_mod

# ------------------------------------------------------------------
# Muat scraper.py ASLI secara terisolasi (di bawah package sintetis).
#
# Tujuan: test ini menguji kode scraper yang sebenarnya, tetapi tidak boleh
# bergantung pada stub `includes.tiktok_scrape_videos` milik test lain
# (test_video_analytics_growth_today men-stub package tsb sehingga submodule
# `scraper` tidak bisa di-import dari sana).
# ------------------------------------------------------------------
_SCRAPER_PKG = "_scraper_under_test"
if _SCRAPER_PKG not in sys.modules:
    _pkg = types.ModuleType(_SCRAPER_PKG)
    _pkg.__path__ = [os.path.join(ROOT_DIR, "includes", "tiktok_scrape_videos")]
    sys.modules[_SCRAPER_PKG] = _pkg

    _driver_mod = types.ModuleType(_SCRAPER_PKG + ".driver")
    _driver_mod.create_driver = lambda *args, **kwargs: None
    sys.modules[_SCRAPER_PKG + ".driver"] = _driver_mod

scraper_mod = importlib.import_module(_SCRAPER_PKG + ".scraper")
TikTokScraper = scraper_mod.TikTokScraper
MAX_VIDEOS = scraper_mod.MAX_VIDEOS
MAX_SCROLLS = scraper_mod.MAX_SCROLLS

import includes.video_analytics.video_analytics as va  # noqa: E402
import routers.creator.video_analytics as rva  # noqa: E402


def _read_source(relative_path):
    with open(os.path.join(ROOT_DIR, relative_path), encoding="utf-8") as handle:
        return handle.read()


def _raw_videos(count):
    """Bikin `count` video mentah dengan bentuk seperti keluaran TikTokScraper."""
    return [
        {
            "id": f"video-{i}",
            "desc": f"caption {i}",
            "views": 1000 + i,
            "likes": 10,
            "comments": 1,
            "shares": 0,
            "upload_date": "2026-09-01 12:00:00",
            "upload_timestamp": 1756700000,
            "duration_sec": 30,
            "thumbnail_url": "",
            "author": "kangpetruk",
            "video_url": f"https://www.tiktok.com/@kangpetruk/video/video-{i}",
        }
        for i in range(count)
    ]


# ==================================================================
# 1. SCRAPER: tidak ada cap artifisial
# ==================================================================
class ScraperHardLimitTestCase(unittest.TestCase):
    """Scraper WAJIB punya hard limit: MAX_VIDEOS (190) unik & MAX_SCROLLS (8)."""

    def _merge_scraper(self, fetched, max_videos=None):
        videos = _raw_videos(fetched)
        if max_videos is None:
            scraper = TikTokScraper("kangpetruk")
        else:
            scraper = TikTokScraper("kangpetruk", max_videos=max_videos)
        scraper._api = {v["id"]: v for v in videos}
        # Sengaja sebagian hanya lewat API (tidak ada di DOM) agar jalur
        # "video dari API yang tidak ada di DOM" juga teruji.
        scraper._dom_order = [v["id"] for v in videos[: len(videos) // 2]]
        scraper._merge()
        return scraper

    def test_default_max_videos_is_hard_cap(self):
        scraper = TikTokScraper("kangpetruk")
        self.assertEqual(scraper.max_videos, MAX_VIDEOS)
        self.assertEqual(MAX_VIDEOS, 190)
        self.assertFalse(hasattr(scraper, "unlimited"))

    def test_zero_no_longer_means_unlimited(self):
        """max_videos=0 harus diperlakukan sebagai MAX_VIDEOS, bukan unlimited."""
        scraper = TikTokScraper("kangpetruk", max_videos=0)
        self.assertEqual(scraper.max_videos, MAX_VIDEOS)

    def test_negative_and_none_fall_back_to_max(self):
        self.assertEqual(TikTokScraper("x", max_videos=-5).max_videos, MAX_VIDEOS)
        self.assertEqual(TikTokScraper("x", max_videos=None).max_videos, MAX_VIDEOS)

    def test_larger_cap_is_clamped(self):
        self.assertEqual(TikTokScraper("x", max_videos=500).max_videos, MAX_VIDEOS)

    def test_smaller_cap_is_honored(self):
        self.assertEqual(TikTokScraper("x", max_videos=90).max_videos, 90)

    def test_merge_caps_unique_videos_to_max(self):
        """195 -> 190, 220 -> 190, 500 -> 190 (hard cap video unik)."""
        for fetched in (195, 220, 500):
            with self.subTest(fetched=fetched):
                scraper = self._merge_scraper(fetched)
                self.assertEqual(len(scraper.videos), MAX_VIDEOS)

    def test_merge_keeps_all_when_below_cap(self):
        scraper = self._merge_scraper(87)
        self.assertEqual(len(scraper.videos), 87)

    def test_merge_respects_smaller_explicit_cap(self):
        scraper = self._merge_scraper(195, max_videos=90)
        self.assertEqual(len(scraper.videos), 90)

    def test_scroll_never_exceeds_max_scrolls(self):
        """Loop scroll tidak boleh lebih dari MAX_SCROLLS (tidak ada scroll ke-9)."""

        class FakeDriver:
            def __init__(self):
                self.scroll_calls = 0

            def execute_script(self, script):
                if "scrollBy" in script:
                    self.scroll_calls += 1
                    return None
                return 1  # selalu 1 video unik -> target tak pernah tercapai

        scraper = TikTokScraper("kangpetruk")
        driver = FakeDriver()
        scraper._driver = driver
        with mock.patch.object(scraper_mod.time, "sleep", lambda *_: None):
            scraper._scroll_until_done()

        self.assertEqual(MAX_SCROLLS, 8)
        self.assertEqual(driver.scroll_calls, MAX_SCROLLS)

    def test_scroll_stops_immediately_when_target_reached(self):
        """Bila DOM sudah menampilkan MAX_VIDEOS unik, TIDAK ada scroll sama sekali."""

        class FakeDriver:
            def __init__(self):
                self.scroll_calls = 0

            def execute_script(self, script):
                if "scrollBy" in script:
                    self.scroll_calls += 1
                    return None
                return MAX_VIDEOS

        scraper = TikTokScraper("kangpetruk")
        driver = FakeDriver()
        scraper._driver = driver
        with mock.patch.object(scraper_mod.time, "sleep", lambda *_: None):
            scraper._scroll_until_done()

        self.assertEqual(driver.scroll_calls, 0)

    def test_scroll_stops_right_after_reaching_target(self):
        """Begitu target tercapai setelah scroll, berhenti (tidak scroll lagi)."""

        class FakeDriver:
            def __init__(self):
                self.calls = 0
                self.scroll_calls = 0

            def execute_script(self, script):
                if "scrollBy" in script:
                    self.scroll_calls += 1
                    return None
                self.calls += 1
                return 50 if self.calls == 1 else MAX_VIDEOS

        scraper = TikTokScraper("kangpetruk")
        driver = FakeDriver()
        scraper._driver = driver
        with mock.patch.object(scraper_mod.time, "sleep", lambda *_: None):
            scraper._scroll_until_done()

        self.assertEqual(driver.scroll_calls, 1)

    def test_scroll_does_not_divide_by_zero(self):
        """max_videos=0 tidak boleh error saat menghitung progress scroll."""

        class FakeDriver:
            def execute_script(self, script):
                return 3

        scraper = TikTokScraper("kangpetruk", max_videos=0)
        scraper._driver = FakeDriver()

        with mock.patch.object(scraper_mod.time, "sleep", lambda *_: None):
            scraper._scroll_until_done()

        self.assertGreaterEqual(scraper._stalled, 1)

    def test_source_has_hard_limit_constants(self):
        source = _read_source(os.path.join("includes", "tiktok_scrape_videos", "scraper.py"))
        self.assertIn("MAX_VIDEOS = 190", source)
        self.assertIn("MAX_SCROLLS = 8", source)
        self.assertNotIn("MAX_SCROLLS = 500", source)
        self.assertNotIn("UNLIMITED_VIDEOS", source)
        self.assertNotIn("999999", source, "sentinel 999999 harus sudah dihapus")
        self.assertNotIn("[:90]", source)
        self.assertNotIn("[:100]", source)


# ==================================================================
# 2. SERVICE: fetched == processed + metrik kegagalan
# ==================================================================
class _FakeScraper:
    """Pengganti TikTokScraper: mengembalikan `videos` apa adanya."""

    last_kwargs = None
    videos = []

    def __init__(self, username=None, max_videos=0, **kwargs):
        _FakeScraper.last_kwargs = dict(username=username, max_videos=max_videos, **kwargs)
        self.username = username
        self.max_videos = max_videos

    def run(self):
        return list(_FakeScraper.videos)


class ScanCoverageTestCase(unittest.TestCase):
    def setUp(self):
        _FakeScraper.videos = []
        _FakeScraper.last_kwargs = None

    def _run_update(self, fetched, max_videos=MAX_VIDEOS, fail_ids=(), no_id_count=0,
                    use_default=False):
        videos = _raw_videos(fetched)
        for i in range(no_id_count):
            videos[i]["id"] = ""
        _FakeScraper.videos = videos

        writer = {"meta": 0, "snapshots": 0, "snapshot_ids": []}

        def fake_upsert_video(creator_id, video_data):
            writer["meta"] += 1
            return f"pk-{video_data['video_id']}"

        def fake_upsert_stats(video_pk=None, **kwargs):
            video_id = str(video_pk).replace("pk-", "")
            if video_id in fail_ids:
                raise RuntimeError("db error simulasi")
            writer["snapshots"] += 1
            writer["snapshot_ids"].append(video_id)
            return True

        with mock.patch.object(va, "get_creator",
                               lambda cid: {"id": cid, "username": "kangpetruk"}), \
                mock.patch.object(va, "TikTokScraper", _FakeScraper), \
                mock.patch.object(va, "upsert_tiktok_video", fake_upsert_video), \
                mock.patch.object(va, "upsert_video_daily_stats", fake_upsert_stats), \
                mock.patch.object(va.video_analytics_service, "_read_analytics",
                                                                    lambda cid: {"total_video": fetched, "videos": [],
                                               "statistics": {}}):
            if use_default:
                result = va.update_creator_analytics(2)
            else:
                result = va.update_creator_analytics(2, max_videos)

        return result, writer

    def test_all_fetched_videos_are_processed_up_to_hard_cap(self):
        """Hasil collection diproses, tetapi DB TIDAK menerima > MAX_VIDEOS."""
        cases = {195: MAX_VIDEOS, 220: MAX_VIDEOS, 87: 87}
        for fetched, expected in cases.items():
            with self.subTest(fetched=fetched):
                result, writer = self._run_update(fetched)

                self.assertTrue(result["success"])
                self.assertEqual(result["fetched"], expected)
                self.assertEqual(result["filtered"], expected)
                self.assertEqual(result["processed"], expected)
                self.assertEqual(result["processed_success"], expected)
                self.assertEqual(result["processed_failed"], 0)
                self.assertEqual(result["snapshots_written"], expected)
                self.assertEqual(result["skipped_no_id"], 0)
                self.assertEqual(result["failures"], [])

                # Bukti nyata: DB writer TIDAK pernah dipanggil > MAX_VIDEOS
                self.assertLessEqual(writer["meta"], MAX_VIDEOS)
                self.assertEqual(writer["meta"], expected)
                self.assertEqual(writer["snapshots"], expected)
                self.assertEqual(len(writer["snapshot_ids"]), expected)

    def test_scraper_called_with_hard_cap(self):
        """Service meneruskan hard cap MAX_VIDEOS ke scraper (bukan 0)."""
        self._run_update(195, max_videos=0)
        self.assertIsNotNone(_FakeScraper.last_kwargs)
        self.assertEqual(_FakeScraper.last_kwargs["max_videos"], MAX_VIDEOS)
        self.assertEqual(_FakeScraper.last_kwargs["username"], "kangpetruk")

    def test_service_default_uses_hard_cap(self):
        """Memanggil service tanpa argumen harus memakai MAX_VIDEOS."""
        self._run_update(195, use_default=True)
        self.assertIsNotNone(_FakeScraper.last_kwargs)
        self.assertEqual(_FakeScraper.last_kwargs["max_videos"], MAX_VIDEOS)

    def test_smaller_explicit_cap_is_honored(self):
        """Cap eksplisit lebih kecil dari MAX_VIDEOS tetap dihormati."""
        self._run_update(195, max_videos=90)
        self.assertEqual(_FakeScraper.last_kwargs["max_videos"], 90)

    def test_larger_explicit_cap_is_clamped(self):
        """Cap eksplisit > MAX_VIDEOS dijepit ke MAX_VIDEOS."""
        self._run_update(195, max_videos=999)
        self.assertEqual(_FakeScraper.last_kwargs["max_videos"], MAX_VIDEOS)

    def test_failed_video_is_reported_not_silently_dropped(self):
        """Video yang gagal diproses dilaporkan sebagai failure (setelah cap)."""
        fetched = 195
        expected = MAX_VIDEOS  # hasil collection dipotong ke hard cap 190
        fail_ids = {"video-7"}
        result, writer = self._run_update(fetched, fail_ids=fail_ids)

        self.assertEqual(result["fetched"], expected)
        self.assertEqual(result["processed"], expected)
        self.assertEqual(result["processed_failed"], 1)
        self.assertEqual(result["processed_success"], expected - 1)
        self.assertEqual(result["snapshots_written"], expected - 1)
        self.assertEqual(writer["snapshots"], expected - 1)

        # Kegagalan tidak disembunyikan
        self.assertEqual(len(result["failures"]), 1)
        self.assertEqual(result["failures"][0]["video_id"], "video-7")
        self.assertIn("db error simulasi", result["failures"][0]["error"])

    def test_video_without_id_reported(self):
        """Video tanpa id tidak bisa diproses, tetapi tetap dilaporkan."""
        fetched = 87
        result, _writer = self._run_update(fetched, no_id_count=1)

        self.assertEqual(result["fetched"], fetched)
        self.assertEqual(result["skipped_no_id"], 1)
        self.assertEqual(result["processed"], fetched - 1)
        self.assertEqual(result["processed_success"], fetched - 1)
        self.assertTrue(result["failures"])

    def test_coverage_metrics_are_distinct_values(self):
        """fetched/processed/success/failed/snapshot_written harus terpisah."""
        result, writer = self._run_update(195, fail_ids={"video-3", "video-4"})

        self.assertEqual(result["fetched"], MAX_VIDEOS)      # 195 -> 190 (cap)
        self.assertEqual(result["processed"], MAX_VIDEOS)    # semua dicoba
        self.assertEqual(result["processed_success"], MAX_VIDEOS - 2)
        self.assertEqual(result["processed_failed"], 2)
        self.assertEqual(result["snapshots_written"], MAX_VIDEOS - 2)
        self.assertEqual(writer["snapshots"], MAX_VIDEOS - 2)
        self.assertNotEqual(result["processed"], result["snapshots_written"])


# ==================================================================
# 3. ROUTER: tidak memakai angka hardcoded lagi
# ==================================================================
class RouterHardLimitTestCase(unittest.TestCase):
    def test_router_source_no_unlimited_max_videos(self):
        source = _read_source(os.path.join("routers", "creator", "video_analytics.py"))
        self.assertNotIn("max_videos = 0", source)
        self.assertNotIn("max_videos = 90", source)
        self.assertNotIn("max_videos = 195", source)
        # Router memakai default service (yang sudah menerapkan hard cap).
        self.assertIn("update_creator_analytics(creator_id)", source)

    def test_video_performance_scanner_uses_hard_cap(self):
        source = _read_source(os.path.join("includes", "video_performance", "scanner.py"))
        self.assertNotIn("scroll_count * 10", source)
        # Hanya komentar yang boleh menyebut max_videos=0; pemanggilan scraper
        # tidak boleh lagi memakai cap 0 (tanpa argumen koma).
        self.assertNotIn("max_videos=0,", source)
        self.assertIn("max_videos=MAX_VIDEOS", source)

    def test_update_endpoint_uses_hard_cap_default(self):
        captured = {}

        def fake_update(creator_id):
            captured["creator_id"] = creator_id
            return {
                "success": True,
                "fetched": MAX_VIDEOS,
                "processed": MAX_VIDEOS,
                "processed_success": MAX_VIDEOS,
                "processed_failed": 0,
                "snapshots_written": MAX_VIDEOS,
            }

        with mock.patch.object(rva, "update_creator_analytics", fake_update), \
                mock.patch.object(rva, "match_tiktok_videos_to_jobs", lambda: MAX_VIDEOS), \
                mock.patch.object(rva, "jsonify", lambda payload: payload):
            response = rva.video_analytics_update(2)

        self.assertEqual(captured["creator_id"], 2)

        # Counter coverage ikut terkirim ke client (JSON response)
        self.assertEqual(response["fetched"], MAX_VIDEOS)
        self.assertEqual(response["processed"], MAX_VIDEOS)
        self.assertEqual(response["snapshots_written"], MAX_VIDEOS)


if __name__ == "__main__":
    unittest.main()
