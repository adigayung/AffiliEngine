"""VideoPerformanceService - Orchestration Layer.

Mengkoordinasikan alur bisnis sesuai arsitektur baru:

Flow yang benar:
1. Scan Akun TikTok -> ambil seluruh video
2. Simpan/update data video TikTok (tiktok_videos)
3. Simpan statistik harian (tiktok_video_stats)
4. Matching ke upload_jobs (hanya sebagai relasi)
5. Selesai

Source of Truth: Akun TikTok, BUKAN upload_jobs.
"""

from includes.mysql import (
    get_creator,
    upsert_tiktok_video,
    upsert_video_daily_stats,
    match_video_to_upload_job,
)


class VideoPerformanceService:
    """
    Service layer untuk mengkoordinasikan scan flow.

    Service TIDAK lagi bergantung pada MatchingEngine yang kompleks.
    Matching sekarang sederhana: cari upload_job terdekat yang sudah uploaded.
    """

    def __init__(self, manager=None, scanner=None, matching=None):
        self.manager = manager
        self.scanner = scanner
        # matching dipertahankan untuk backward compatibility
        self.matching = matching

    def run_scan(self, creator_id: int) -> bool:
        """
        Jalankan full scan flow untuk creator.
        Ini akan dipanggil oleh background thread.

        Flow baru:
        1. Validasi creator & ambil username
        2. Scanner.scan(username) -> list video dari TikTok
           - Dengan CAPTCHA awareness
        3. Untuk setiap video:
           a. upsert_tiktok_video() -> INSERT atau UPDATE data video
           b. upsert_video_daily_stats() -> INSERT atau UPDATE statistik harian
           c. match_video_to_upload_job() -> coba match ke upload_jobs
        4. Selesai

        Args:
            creator_id: ID creator dari tabel creators

        Returns:
            bool: True jika berhasil
        """
        mgr = self.manager
        if not mgr:
            return False

        try:
            # --- Step 1: Validasi Creator ---
            creator = get_creator(creator_id)
            if not creator:
                mgr.error(f"Creator ID {creator_id} tidak ditemukan di database.")
                return False

            username = creator.get("username", "").strip()
            if not username:
                mgr.error(f"Creator ID {creator_id} tidak memiliki username.")
                return False

            mgr.add_log(f"Memulai scan untuk @{username}", "info")
            mgr.set_progress(5)

            # --- Step 2: Scan TikTok dengan CAPTCHA Awareness ---
            if not self.scanner:
                mgr.error("Scanner tidak tersedia.")
                return False

            mgr.add_log(f"Membuka profil TikTok @{username} ...", "info")
            mgr.set_progress(10)

            # CAPTCHA-aware callbacks
            def _on_captcha_started():
                mgr.waiting_captcha()
                mgr.add_log("CAPTCHA terdeteksi.", "warning")
                mgr.add_log("Menunggu CAPTCHA diselesaikan...", "warning")

            def _on_captcha_finished():
                mgr.captcha_resolved()
                mgr.add_log("CAPTCHA selesai.", "success")
                mgr.add_log("Melanjutkan proses scan...", "success")

            def _on_captcha_timeout():
                mgr.add_log("CAPTCHA tidak dapat diselesaikan.", "danger")
                mgr.error("CAPTCHA tidak dapat diselesaikan dalam batas waktu.")

            def _on_captcha_browser_closed():
                mgr.add_log("Browser ditutup saat menunggu CAPTCHA.", "danger")
                mgr.error("Browser ditutup saat menunggu CAPTCHA.")

            videos = self.scanner.scan_with_captcha_awareness(
                username=username,
                on_captcha_started=_on_captcha_started,
                on_captcha_finished=_on_captcha_finished,
                on_captcha_timeout=_on_captcha_timeout,
                on_captcha_browser_closed=_on_captcha_browser_closed,
            )

            if videos is None:
                return False

            if len(videos) == 0:
                if mgr.state in ("failed",):
                    return False
                if mgr.state == "waiting_captcha":
                    mgr.captcha_resolved()
                mgr.add_log("Tidak ada video yang ditemukan di profil.", "warning")
                mgr.finish()
                return True

            if mgr.state == "waiting_captcha":
                mgr.captcha_resolved()

            mgr.add_log(f"Ditemukan {len(videos)} video dari @{username}", "success")
            mgr.set_progress(30)

            # --- Debug Log: detail video hasil scan ---
            if videos:
                # Urutkan berdasarkan upload_time
                sorted_videos = sorted(
                    [v for v in videos if v.get("upload_time")],
                    key=lambda v: v.get("upload_time", ""),
                    reverse=True,
                )
                video_pertama = sorted_videos[0] if sorted_videos else videos[0]
                video_terakhir = sorted_videos[-1] if sorted_videos else videos[-1]

                mgr.add_log(
                    f"[DEBUG] ====== LAPORAN SCAN @{username} ======",
                    "info"
                )
                mgr.add_log(
                    f"[DEBUG] Total video dari scanner: {len(videos)}",
                    "info"
                )
                mgr.add_log(
                    f"[DEBUG] Video PERTAMA (terbaru): "
                    f"ID={video_pertama.get('video_id','?')} | "
                    f"Upload={video_pertama.get('upload_time','?')} | "
                    f"Caption={video_pertama.get('caption','?')[:50]}",
                    "info"
                )
                mgr.add_log(
                    f"[DEBUG] Video TERAKHIR (terlama): "
                    f"ID={video_terakhir.get('video_id','?')} | "
                    f"Upload={video_terakhir.get('upload_time','?')} | "
                    f"Caption={video_terakhir.get('caption','?')[:50]}",
                    "info"
                )
                mgr.add_log(
                    f"[DEBUG] ====== AKHIR LAPORAN SCAN ======",
                    "info"
                )
            else:
                mgr.add_log("[DEBUG] Tidak ada video dari scanner.", "warning")

            # --- Step 3: Proses setiap video ---
            total = len(videos)
            for idx, video in enumerate(videos):
                # Cek stop request
                if mgr.stop_requested:
                    mgr.add_log("Scan dihentikan oleh pengguna.", "warning")
                    mgr.running = False
                    return False

                video_id = video.get("video_id", "")
                if not video_id:
                    continue

                # 3a. Simpan/update data video TikTok
                try:
                    video_pk = upsert_tiktok_video(creator_id, video)
                except Exception as e:
                    mgr.add_log(
                        f"Gagal menyimpan video {video_id}: {e}",
                        "danger"
                    )
                    continue

                # 3b. Simpan statistik harian
                views = video.get("views", 0) or 0
                likes = video.get("likes", 0) or 0
                comments = video.get("comments", 0) or 0
                shares = video.get("shares", 0) or 0

                try:
                    upsert_video_daily_stats(
                        video_pk,
                        views=views,
                        likes=likes,
                        comments=comments,
                        shares=shares,
                    )
                except Exception as e:
                    mgr.add_log(
                        f"Gagal menyimpan stats video {video_id}: {e}",
                        "danger"
                    )

                # 3c. Matching ke upload_jobs (hanya relasi, bukan source of truth)
                try:
                    match_result = match_video_to_upload_job(creator_id, video_id)
                    if match_result:
                        mgr.add_log(
                            f"Video {video_id} ter-match dengan upload job "
                            f"#{match_result['upload_job_id']}",
                            "info"
                        )
                except Exception as e:
                    # Matching gagal bukan error kritis
                    pass

                progress = 30 + int((idx + 1) / total * 65)
                mgr.set_progress(progress)

            mgr.add_log(
                f"Semua {total} video berhasil diproses.",
                "success"
            )
            mgr.set_progress(100)

            # --- Selesai ---
            mgr.finish()
            return True

        except Exception as e:
            mgr.error(f"Scan gagal: {e}")
            return False