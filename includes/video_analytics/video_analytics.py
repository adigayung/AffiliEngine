"""
Video Analytics Service Layer.

Service Layer yang menangani seluruh business logic Video Analytics.
Router hanya memanggil fungsi di module ini dan merender template.

Tanggung Jawab:
    - Menerima creator_id dari Router
    - Mengambil data creator (validasi)
    - Membaca data analytics dari database (jika tersedia)
    - Membentuk object yang siap digunakan template
    - Mengembalikan object ke Router

TIDAK menangani:
    - Scraping TikTok
    - Update Analytics
    - INSERT/UPDATE/DELETE database
    - Background job
"""

from datetime import datetime
from includes.mysql import get_connection, get_creator
from includes.mysql import upsert_tiktok_video, upsert_video_daily_stats
from includes.tiktok_scrape_videos import TikTokScraper
from includes.logFX import logger, INFO, WARNING, ERROR

# ==============================
# KONSTANTA LOG PREFIX
# ==============================
LOG_PREFIX = "[VideoAnalytics]"


class VideoAnalyticsService:
    """
    Service Layer untuk Video Analytics.

    Seluruh workflow Video Analytics berada di class ini.
    Router cukup memanggil .index(creator_id) dan merender template.
    """

    def index(self, creator_id: int) -> dict:
        """
        Entry point utama untuk halaman Video Analytics.

        Workflow:
            1. Validasi creator
            2. Baca data analytics dari database (jika tersedia)
            3. Bentuk object siap template
            4. Kembalikan dict

        Args:
            creator_id: ID creator dari tabel creators

        Returns:
            dict: Data siap render, atau None jika creator tidak ditemukan
        """
        try:
            # ==============================
            # STEP 1: LOAD CREATOR
            # ==============================
            logger(INFO, f"{LOG_PREFIX} Load creator {creator_id}")

            creator = get_creator(creator_id)
            if not creator:
                logger(WARNING, f"{LOG_PREFIX} Creator {creator_id} tidak ditemukan")
                return None

            logger(INFO, f"{LOG_PREFIX} Creator ditemukan: "
                         f"{creator.get('username', 'unknown')}")

            # ==============================
            # STEP 2: BACA DATA ANALYTICS
            # ==============================
            logger(INFO, f"{LOG_PREFIX} Membaca data analytics untuk creator {creator_id}")

            analytics = self._read_analytics(creator_id)

            if analytics["total_video"] == 0:
                logger(INFO, f"{LOG_PREFIX} Data analytics belum tersedia untuk creator {creator_id}")
            else:
                logger(INFO, f"{LOG_PREFIX} Data analytics ditemukan: "
                             f"{analytics['total_video']} video")

            # ==============================
            # STEP 3: BENTUK OBJECT
            # ==============================
            result = {
                "creator": creator,
                "statistics": analytics.get("statistics", {}),
                "videos": analytics.get("videos", []),
                "last_update": analytics.get("last_update", None),
                "total_video": analytics.get("total_video", 0),
                "status": analytics.get("status", "no_data"),
            }

            logger(INFO, f"{LOG_PREFIX} Render selesai untuk creator {creator_id}")
            return result

        except Exception as e:
            logger(ERROR, f"{LOG_PREFIX} ERROR saat memproses creator {creator_id}: {e}")
            # Tetap kembalikan data default, jangan raise exception
            return self._empty_result(creator_id)

    def update_creator_analytics(self, creator_id: int, max_videos: int) -> dict:
        """
        Update analytics untuk satu Creator.

        Workflow:
            1. Validasi creator
            2. Scrape seluruh video terbaru dari TikTok
            3. Sinkronisasi ke tiktok_videos (INSERT/UPDATE metadata)
            4. Simpan snapshot statistik ke tiktok_video_stats
            5. Baca kembali analytics terbaru dari database
            6. Kembalikan result

        Args:
            creator_id: ID creator dari tabel creators

        Returns:
            dict: {
                "success": bool,
                "message": str,
                "creator_id": int,
                "total_videos": int,
                "new_videos": int,
                "updated_videos": int,
            }
        """
        try:
            # ==============================
            # STEP 1: VALIDASI CREATOR
            # ==============================
            logger(INFO, f"{LOG_PREFIX} Mulai update analytics untuk creator {creator_id}")

            creator = get_creator(creator_id)
            if not creator:
                logger(WARNING, f"{LOG_PREFIX} Creator {creator_id} tidak ditemukan")
                return {
                    "success": False,
                    "message": "Creator tidak ditemukan.",
                    "creator_id": creator_id,
                    "total_videos": 0,
                    "new_videos": 0,
                    "updated_videos": 0,
                }

            username = creator.get("username", "")
            logger(INFO, f"{LOG_PREFIX} Creator: @{username} (ID: {creator_id})")

            # ==============================
            # STEP 2: SCRAPE TIKTOK
            # ==============================
            logger(INFO, f"{LOG_PREFIX} Memulai scraping TikTok @{username}...")

            scraper = TikTokScraper(
                username=username,
                max_videos=max_videos,  # 0 = semua video
                output_file=False
            )
            scraped_videos = scraper.run()

            if not scraped_videos:
                logger(WARNING, f"{LOG_PREFIX} Scraping tidak menghasilkan video")
                return {
                    "success": False,
                    "message": "Scraping tidak menghasilkan video. Periksa koneksi atau profile Chromium.",
                    "creator_id": creator_id,
                    "total_videos": 0,
                    "new_videos": 0,
                    "updated_videos": 0,
                }

            logger(INFO, f"{LOG_PREFIX} Scraping selesai: {len(scraped_videos)} video ditemukan")

            # ==============================
            # STEP 3: SINKRONISASI DATABASE
            # ==============================
            new_videos = 0
            updated_videos = 0
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for sv in scraped_videos:
                # Map scraper data ke format yang diterima upsert_tiktok_video
                video_data = {
                    "video_id": sv.get("id", ""),
                    "video_url": sv.get("video_url", ""),
                    "caption": sv.get("desc", ""),
                    "upload_time": sv.get("upload_date", None),
                    "duration": sv.get("duration_sec", 0),
                }

                try:
                    # Upsert metadata video (termasuk duration)
                    video_pk = upsert_tiktok_video(creator_id, video_data)

                    # Simpan snapshot statistik (favorites default 0 dari scraper)
                    upsert_video_daily_stats(
                        video_pk=video_pk,
                        views=sv.get("views", 0),
                        likes=sv.get("likes", 0),
                        comments=sv.get("comments", 0),
                        shares=sv.get("shares", 0),
                        favorites=sv.get("favorites", 0),
                        snapshot_time=now_str
                    )
                except Exception as e:
                    logger(ERROR, f"{LOG_PREFIX} Gagal sinkronisasi video {sv.get('id', '?')}: {e}")
                    continue

            logger(INFO, f"{LOG_PREFIX} Sinkronisasi selesai: "
                         f"{len(scraped_videos)} video diproses")

            # ==============================
            # STEP 5: BACA ANALYTICS TERBARU
            # ==============================
            analytics = self._read_analytics(creator_id)
            total_videos = analytics.get("total_video", len(scraped_videos))

            logger(INFO, f"{LOG_PREFIX} Update analytics selesai untuk creator {creator_id}: "
                         f"{total_videos} total video")

            return {
                "success": True,
                "message": "Analytics updated successfully.",
                "creator_id": creator_id,
                "total_videos": total_videos,
                "new_videos": new_videos,
                "updated_videos": updated_videos,
            }

        except Exception as e:
            logger(ERROR, f"{LOG_PREFIX} ERROR saat update analytics creator {creator_id}: {e}")
            return {
                "success": False,
                "message": f"Update analytics gagal: {str(e)}",
                "creator_id": creator_id,
                "total_videos": 0,
                "new_videos": 0,
                "updated_videos": 0,
            }

    def _read_analytics(self, creator_id: int) -> dict:
        """
        Baca data analytics dari database.

        Membaca data dari:
            - tiktok_videos (metadata video: caption, upload_time, duration)
            - tiktok_video_stats (statistik + growth dari 2 snapshot terakhir)

        Growth dihitung dari selisih snapshot terbaru dan snapshot sebelumnya.
        Jika hanya tersedia satu snapshot, growth = 0.

        Args:
            creator_id: ID creator

        Returns:
            dict: Data analytics dengan growth
        """
        try:
            conn = get_connection()
            try:
                with conn.cursor() as cursor:
                    # ==============================
                    # AMBIL DAFTAR VIDEO + DURATION
                    # ==============================
                    cursor.execute("""
                        SELECT
                            v.id,
                            v.video_id,
                            v.video_url,
                            v.caption,
                            v.upload_time,
                            v.last_scan,
                            v.duration,
                            v.match_score,
                            v.match_method,
                            v.matched_at,
                            v.upload_job_id
                        FROM tiktok_videos v
                        WHERE v.creator_id = %s
                        ORDER BY v.upload_time DESC
                    """, (creator_id,))
                    video_rows = cursor.fetchall()

                    if not video_rows:
                        return self._empty_analytics()

                    total_video = len(video_rows)
                    video_ids = [row["id"] for row in video_rows]
                    placeholders = ",".join(["%s"] * len(video_ids))

                    # ==============================
                    # AMBIL 2 SNAPSHOT TERAKHIR PER VIDEO
                    # ==============================
                    if video_ids:
                        cursor.execute(f"""
                            SELECT
                                s.video_id,
                                s.views,
                                s.likes,
                                s.comments,
                                s.shares,
                                s.favorites,
                                s.snapshot_time,
                                s.created_at
                            FROM tiktok_video_stats s
                            INNER JOIN (
                                SELECT
                                    video_id,
                                    snapshot_time,
                                    ROW_NUMBER() OVER (
                                        PARTITION BY video_id
                                        ORDER BY snapshot_time DESC
                                    ) AS rn
                                FROM tiktok_video_stats
                                WHERE video_id IN ({placeholders})
                            ) latest
                                ON s.video_id = latest.video_id
                                AND s.snapshot_time = latest.snapshot_time
                                AND latest.rn <= 2
                            ORDER BY s.video_id, s.snapshot_time DESC
                        """, video_ids)
                        stats_rows = cursor.fetchall()
                    else:
                        stats_rows = []

                    # ==============================
                    # AMBIL LAST UPDATE
                    # ==============================
                    cursor.execute("""
                        SELECT MAX(last_scan) AS last_scan
                        FROM tiktok_videos
                        WHERE creator_id = %s
                    """, (creator_id,))
                    last_scan_row = cursor.fetchone()
                    last_update = last_scan_row["last_scan"] if last_scan_row else None

                    # ==============================
                    # BENTUK STATS MAP (2 snapshot per video)
                    # ==============================
                    # stats_map[video_id] = {curr: {...}, prev: {...}}
                    stats_map = {}
                    for s in stats_rows:
                        vid = int(s["video_id"])  # VARCHAR → int agar cocok dengan row["id"]
                        if vid not in stats_map:
                            stats_map[vid] = {"curr": None, "prev": None}

                        entry = {
                            "views": s["views"] or 0,
                            "likes": s["likes"] or 0,
                            "comments": s["comments"] or 0,
                            "shares": s["shares"] or 0,
                            "favorites": s["favorites"] or 0,
                            "snapshot_time": s["snapshot_time"],
                        }

                        if stats_map[vid]["curr"] is None:
                            stats_map[vid]["curr"] = entry
                        elif stats_map[vid]["prev"] is None:
                            stats_map[vid]["prev"] = entry

                    # ==============================
                    # HITUNG TOTAL STATISTIK & GROWTH
                    # ==============================
                    total_views = 0
                    total_likes = 0
                    total_comments = 0
                    total_shares = 0
                    total_favorites = 0

                    # ==============================
                    # BENTUK DAFTAR VIDEO
                    # ==============================
                    videos = []
                    for row in video_rows:
                        video_pk = row["id"]
                        stats = stats_map.get(video_pk, {})
                        curr = stats.get("curr", {}) or {}
                        prev = stats.get("prev", {}) or {}

                        # Statistik terkini
                        views = curr.get("views", 0)
                        likes = curr.get("likes", 0)
                        comments = curr.get("comments", 0)
                        shares = curr.get("shares", 0)
                        favorites = curr.get("favorites", 0)

                        # Growth
                        views_growth = views - prev.get("views", views) if prev else 0
                        likes_growth = likes - prev.get("likes", likes) if prev else 0
                        comments_growth = comments - prev.get("comments", comments) if prev else 0
                        shares_growth = shares - prev.get("shares", shares) if prev else 0
                        favorites_growth = favorites - prev.get("favorites", favorites) if prev else 0

                        total_views += views
                        total_likes += likes
                        total_comments += comments
                        total_shares += shares
                        total_favorites += favorites

                        upload_time = row["upload_time"]
                        if isinstance(upload_time, datetime):
                            upload_time_str = upload_time.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            upload_time_str = str(upload_time) if upload_time else None

                        last_scan = row["last_scan"]
                        if isinstance(last_scan, datetime):
                            last_scan_str = last_scan.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            last_scan_str = str(last_scan) if last_scan else None

                        # Format duration ke menit:detik
                        duration_sec = row["duration"]
                        if duration_sec:
                            minutes = duration_sec // 60
                            seconds = duration_sec % 60
                            duration_str = f"{minutes}:{seconds:02d}"
                        else:
                            duration_str = None

                        videos.append({
                            "id": video_pk,
                            "video_id": row["video_id"],
                            "video_url": row["video_url"],
                            "caption": row["caption"],
                            "upload_time": upload_time_str,
                            "last_scan": last_scan_str,
                            "duration": duration_str,
                            "duration_sec": duration_sec,
                            "views": views,
                            "views_growth": views_growth,
                            "likes": likes,
                            "likes_growth": likes_growth,
                            "comments": comments,
                            "comments_growth": comments_growth,
                            "shares": shares,
                            "shares_growth": shares_growth,
                            "favorites": favorites,
                            "favorites_growth": favorites_growth,
                            "snapshot_time": curr.get("snapshot_time"),
                            "match_score": row["match_score"],
                            "match_method": row["match_method"],
                            "upload_job_id": row["upload_job_id"],
                        })

                    # ==============================
                    # FORMAT LAST UPDATE
                    # ==============================
                    last_update_str = None
                    if last_update:
                        if isinstance(last_update, datetime):
                            last_update_str = last_update.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            last_update_str = str(last_update)

                    return {
                        "total_video": total_video,
                        "videos": videos,
                        "last_update": last_update_str,
                        "statistics": {
                            "total_views": total_views,
                            "total_likes": total_likes,
                            "total_comments": total_comments,
                            "total_shares": total_shares,
                            "total_favorites": total_favorites,
                        },
                        "status": "available",
                    }

            finally:
                conn.close()

        except Exception as e:
            logger(ERROR, f"{LOG_PREFIX} ERROR membaca analytics: {e}")
            return self._empty_analytics()

    def _empty_analytics(self) -> dict:
        """
        Kembalikan object analytics kosong.

        Returns:
            dict: Data analytics dengan placeholder
        """
        return {
            "total_video": 0,
            "videos": [],
            "last_update": None,
            "statistics": {
                "total_views": 0,
                "total_likes": 0,
                "total_comments": 0,
                "total_shares": 0,
                "total_favorites": 0,
            },
            "status": "no_data",
        }

    def _empty_result(self, creator_id: int) -> dict:
        """
        Kembalikan result kosong untuk error handling.

        Args:
            creator_id: ID creator

        Returns:
            dict: Data dengan placeholder
        """
        return {
            "creator": {"id": creator_id, "username": "Unknown", "display_name": "Unknown"},
            "statistics": {
                "total_views": 0,
                "total_likes": 0,
                "total_comments": 0,
                "total_shares": 0,
                "total_favorites": 0,
            },
            "videos": [],
            "last_update": None,
            "total_video": 0,
            "status": "error",
        }


# ==============================
# SINGLETON INSTANCE
# ==============================
video_analytics_service = VideoAnalyticsService()


# ==============================
# STANDALONE FUNCTION
# ==============================
def update_creator_analytics(creator_id: int, max_videos: int = 0) -> dict:
    """
    Update analytics untuk satu Creator.

    Router cukup memanggil fungsi ini tanpa perlu mengetahui
    detail implementasi di dalamnya.

    Args:
        creator_id: ID creator dari tabel creators
        max_videos: Jumlah maksimal video yang di-scrape (0 = semua)

    Returns:
        dict: {
            "success": bool,
            "message": str,
            "creator_id": int,
            "total_videos": int,
            "new_videos": int,
            "updated_videos": int,
        }
    """
    return video_analytics_service.update_creator_analytics(creator_id, max_videos)
