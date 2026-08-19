# File : includes\facebook_upload_manager.py
"""
facebook_upload_manager.py — Manager background Facebook Uploader.

Mengikuti pola UploadManager (TikTok) tetapi mengeksekusi FacebookUploader
(package includes/facebook_uploader/) langsung dari Python thread, karena
module Facebook bersifat lokal (tidak melalui WebSocket / Android).

SATU START = SATU SESI SELENIUM UNTUK SELURUH BATCH:

    worker membuka SATU driver di awal batch
        -> setiap job memakai driver yang sama via FacebookUploader(driver=driver)
        -> driver ditutup SATU KALI di akhir batch (finally)

Browser lifecycle sepenuhnya di tangan manager (level BATCH), bukan per-job.
Package includes/facebook_uploader TIDAK diubah — API FacebookUploader(driver=...)
sudah mendukung external driver (tidak membuka/menutup browser bila driver
disuplai dari luar, owns_browser=False).
"""

import json
import os
import threading
from datetime import datetime

from includes.facebook_paths import validate_facebook_path
from includes.facebook_uploader import (
    FacebookUploader,
    build_job_data,
    load_schedule,
    validate_schedule_data,
)
from includes.facebook_uploader.browser import (
    DEFAULT_PROFILE_PATH,
    close_browser,
    open_browser,
)
from includes.facebook_uploader.uploader import FB_REELS_URL


class FacebookUploadManager:

    def __init__(self):
        self.running = False
        self.progress = 0
        self.logs = []              # log runtime (start / upload / hasil)
        self.validation_logs = []   # log validasi dari get_paths
        self.jobs = []
        self.thread = None
        self.driver = None          # SATU driver Selenium per batch

        self.stop_requested = False
        self._lock = threading.Lock()

        self.total_jobs_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.current_job_path = None
        self.current_schedule_data = None
        self.current_job_index = 0

    # ============================================================
    # Log — pola HTML sama dengan UploadManager TikTok
    # ============================================================

    def _safe_print(self, text):
        """Print ke console tanpa crash pada encoding cp1252 (Windows)."""
        now = datetime.now().strftime("%H:%M:%S")
        try:
            print(f"[{now}] {text}")
        except UnicodeEncodeError:
            safe = text.encode("ascii", "replace").decode("ascii")
            print(f"[{now}] {safe}")

    def _make_log(self, text, level="info"):
        now = datetime.now().strftime("%H:%M:%S")

        colors = {
            "info": "#4dabf7",
            "valid": "#51cf66",
            "success": "#51cf66",
            "skip": "#fcc419",
            "completed": "#9775fa",
            "warning": "#fcc419",
            "danger": "#ff6b6b",
            "error": "#ff6b6b",
        }
        icons = {
            "info": "\U0001f5c8\ufe0f",
            "valid": "\u2705",
            "success": "\u2705",
            "skip": "\u26a0\ufe0f",
            "completed": "\u2714\ufe0f",
            "warning": "\u26a0\ufe0f",
            "danger": "\u274c",
            "error": "\u274c",
        }

        color = colors.get(level, "#ffffff")
        icon = icons.get(level, "\u2022")

        html = (
            f'<div style="line-height:1.25">'
            f'<span style="color:#666">[{now}]</span> '
            f'<span style="color:{color}">{icon}</span> '
            f'<span>{text}</span>'
            f'</div>'
        )
        return html

    def add_log(self, text, level="info"):
        self.logs.append(self._make_log(text, level))
        if len(self.logs) > 300:
            self.logs = self.logs[-300:]
        self._safe_print(text)

    def add_validation_log(self, text, level="info"):
        self.validation_logs.append(self._make_log(text, level))
        if len(self.validation_logs) > 300:
            self.validation_logs = self.validation_logs[-300:]
        self._safe_print(text)

    def set_validation_logs(self, details):
        """Simpan log validasi dari get_paths (list of (level, text))."""
        self.validation_logs.clear()
        for level, text in details:
            self.add_validation_log(text, level)

    # ============================================================
    # Start — re-validasi ulang path dari textbox (READ-ONLY)
    # ============================================================

    def start(self, path_list):
        with self._lock:
            if self.running:
                # JANGAN buat worker/browser kedua.
                return {
                    "success": False,
                    "message": "Upload masih berjalan. Tekan STOP untuk menghentikan batch.",
                    "code": "already_running",
                }

            self.jobs.clear()
            self.stop_requested = False
            self.logs.clear()

            seen = set()
            for line in (path_list or "").splitlines():
                path = line.strip()
                if not path or path in seen:
                    continue
                seen.add(path)

                # Validasi ulang: kondisi file/status yang berubah setelah
                # halaman dibuka tetap aman. Tidak mengubah schedule.json.
                result = validate_facebook_path(path)

                if result["status"] == "valid":
                    self.jobs.append(path)
                elif result["status"] == "completed":
                    name = result["video_name"] or os.path.basename(path.rstrip("\\/")) or path
                    self.add_log(f"[COMPLETED] {name} — {result['reason']}", "completed")
                else:
                    name = result["video_name"] or os.path.basename(path.rstrip("\\/")) or path
                    self.add_log(f"[SKIP] {name} — {result['reason']}", "skip")

            if not self.jobs:
                self.add_log("[INFO] Tidak ada project valid untuk di-upload ke Facebook.", "info")
                return {
                    "success": False,
                    "message": "Tidak ada project valid untuk di-upload. Periksa log validasi.",
                }

            self.running = True
            self.progress = 0
            self.total_jobs_count = len(self.jobs)
            self.success_count = 0
            self.failed_count = 0
            self.current_job_path = None
            self.current_schedule_data = None
            self.current_job_index = 0
            self.driver = None

            self.add_log(
                f"[INFO] Facebook batch started: {len(self.jobs)} job(s) siap di-upload.",
                "success",
            )

            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()

            return {
                "success": True,
                "total_job": len(self.jobs),
            }

    # ============================================================
    # Worker — SATU Sesi Selenium untuk seluruh batch
    # ============================================================

    def _worker(self):
        driver = None
        try:
            # Thread-safety: periksa stop SEBELUM browser dibuat.
            # Menutup race START -> STOP sebelum worker benar-benar mulai.
            if self.stop_requested:
                return

            driver = open_browser(
                profile_path=DEFAULT_PROFILE_PATH,
                url=FB_REELS_URL,
            )
            self.driver = driver
            self.add_log("[INFO] Selenium browser opened for batch", "info")

            total = self.total_jobs_count
            job_number = 0

            while self.jobs and not self.stop_requested:
                job_path = self.jobs[0]
                self.current_job_path = job_path
                self.current_schedule_data = None
                job_number += 1
                self.current_job_index = job_number

                try:
                    schedule_path = os.path.join(job_path, "schedule.json")
                    data = load_schedule(schedule_path)
                    fb_status = validate_schedule_data(data)

                    if fb_status == "success":
                        self.add_log(
                            f"[COMPLETED] Job {job_number}/{total} — facebook_schedule.status = success",
                            "completed",
                        )
                        self._advance()
                        continue

                    self.current_schedule_data = data
                    job_data = build_job_data(data, job_path)

                    self.add_log(
                        f"[INFO] Starting job {job_number}/{total}: {job_data['video_name']}",
                        "info",
                    )
                    self.add_log(
                        f"[INFO]   Facebook schedule: {job_data['facebook_schedule']}",
                        "info",
                    )
                    self.add_log(
                        f"[INFO]   Affiliate link: {job_data['affiliate_link']}",
                        "info",
                    )

                    # REUSE driver yang sama untuk semua job (browser persistent).
                    uploader = FacebookUploader(driver=driver)
                    result = uploader.run(job_data)

                    if result["success"]:
                        self.add_log("[INFO] FacebookUploader result: success=True", "info")
                        self.add_log("[INFO] Facebook upload completed successfully", "info")
                        self.add_log("[INFO] Updating facebook_schedule.status -> success", "info")

                        # Persistence: HANYA setelah keseluruhan run() sukses.
                        marked = self._mark_facebook_success(job_path)

                        if marked:
                            self.add_log(
                                f"[SUCCESS] Job {job_number}/{total} completed successfully — {job_data['video_name']}",
                                "success",
                            )
                            self.success_count += 1
                            self._advance()
                        else:
                            # Upload sukses tapi persistence gagal — JANGAN
                            # anggap job sukses, agar project tidak dianggap
                            # berhasil padahal status belum tersimpan
                            # (mencegah upload ulang di batch berikutnya).
                            self.add_log(
                                "[ERROR] Gagal menyimpan status success — job TIDAK dianggap sukses (status tetap pending).",
                                "error",
                            )
                            self.failed_count += 1
                            if self._driver_alive(driver):
                                self._advance()
                            else:
                                self.add_log("[ERROR] Selenium session hilang, batch dihentikan.", "error")
                                break
                    else:
                        stage = result.get("stage", "?")
                        error = result.get("error", "?")
                        self.add_log("[ERROR] FacebookUploader result: success=False", "error")
                        self.add_log(
                            f"[ERROR] Job {job_number}/{total} failed: stage={stage} — {error}",
                            "error",
                        )
                        self.add_log("[INFO] facebook_schedule.status remains pending", "info")
                        self.failed_count += 1
                        if self._driver_alive(driver):
                            self.add_log("[INFO] Driver masih valid, lanjut ke job berikutnya.", "info")
                            self._advance()
                        else:
                            self.add_log("[ERROR] Selenium session hilang, batch dihentikan.", "error")
                            break

                except Exception as exc:
                    self.add_log(f"[ERROR] Gagal memproses job: {job_path}", "error")
                    self.add_log(f"[ERROR] {exc}", "error")
                    self.failed_count += 1
                    if not self._driver_alive(driver):
                        self.add_log("[ERROR] Selenium session hilang, batch dihentikan.", "error")
                        break
                    self._advance()

            # Selesai normal / karena stop
            if self.stop_requested:
                self.add_log("[INFO] Stopping Facebook batch", "warning")
                pending = len(self.jobs)
                if pending > 0:
                    self.add_log(f"[INFO] Pending jobs cancelled: {pending}", "warning")
                self.jobs.clear()
            elif not self.jobs:
                self.add_log("[INFO] All Facebook jobs completed", "success")

        finally:
            # Tutup browser SATU KALI di akhir batch (level BATCH, bukan job).
            if driver is not None:
                self.add_log("[INFO] Closing Selenium browser", "info")
                try:
                    close_browser(driver)
                except Exception as exc:
                    self.add_log(f"[ERROR] Gagal menutup browser: {exc}", "error")
                self.driver = None

            self.running = False
            self.thread = None
            self.current_job_path = None
            self.current_schedule_data = None
            self.current_job_index = 0

            if self.stop_requested:
                self.add_log("[INFO] Facebook batch stopped by user", "warning")

            self.stop_requested = False

    @staticmethod
    def _driver_alive(driver):
        """Cek apakah sesi Selenium masih hidup (tanpa memodifikasi state)."""
        if driver is None:
            return False
        try:
            _ = driver.current_url
            return True
        except Exception:
            return False

    def _advance(self):
        """Lanjut ke job berikutnya."""
        if self.jobs:
            self.jobs.pop(0)
        self.progress = 0
        self.current_job_path = None
        self.current_schedule_data = None

    # ============================================================
    # Persistence — tandai facebook_schedule.status = "success"
    # ============================================================

    def _mark_facebook_success(self, project_path):
        """
        Tandai facebook_schedule.status = "success" pada schedule.json project.

        SATU-SATUNYA operasi write manager terhadap schedule.json.
        HANYA mengubah data["facebook_schedule"]["status"]; field lain dan
        format file (indent=4, ensure_ascii=False) dipertahankan — sama seperti
        write_json di includes/schedule/folder.py.

        Read -> Modify -> Write secara aman (temp file + os.replace atomic).
        Tidak membuat schedule.json baru; file tetap di path yang sama.

        Return:
            True  -> status berhasil ditulis & diverifikasi.
            False -> gagal (file hilang / JSON corrupt / struktur invalid /
                      gagal tulis / verifikasi gagal).
        """
        schedule_path = os.path.join(project_path, "schedule.json")

        # --- Read ---
        try:
            with open(schedule_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.add_log(f"[ERROR] schedule.json tidak ditemukan: {schedule_path}", "error")
            return False
        except json.JSONDecodeError as exc:
            self.add_log(
                f"[ERROR] schedule.json corrupt: {schedule_path}\n  Detail: {exc}",
                "error",
            )
            return False
        except OSError as exc:
            self.add_log(
                f"[ERROR] Tidak dapat membaca schedule.json: {schedule_path}\n  Detail: {exc}",
                "error",
            )
            return False

        # --- Pastikan facebook_schedule ada ---
        fb = data.get("facebook_schedule")
        if not isinstance(fb, dict):
            self.add_log(
                f"[ERROR] facebook_schedule tidak ditemukan / invalid: {schedule_path}",
                "error",
            )
            return False

        # --- Modify: HANYA status ---
        fb["status"] = "success"

        # --- Write aman (temp + replace, atomic) ---
        tmp_path = schedule_path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            os.replace(tmp_path, schedule_path)
        except OSError as exc:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
            self.add_log(
                f"[ERROR] Gagal menulis schedule.json: {schedule_path}\n  Detail: {exc}",
                "error",
            )
            return False

        # --- Verifikasi hasil write ---
        try:
            with open(schedule_path, "r", encoding="utf-8") as f:
                check = json.load(f)
            if check.get("facebook_schedule", {}).get("status") != "success":
                self.add_log(
                    f"[ERROR] Verifikasi gagal — status bukan 'success': {schedule_path}",
                    "error",
                )
                return False
        except Exception as exc:
            self.add_log(
                f"[ERROR] Verifikasi hasil write gagal: {schedule_path}\n  Detail: {exc}",
                "error",
            )
            return False

        self.add_log(f"[INFO] Facebook schedule marked success: {schedule_path}", "info")
        return True

    # ============================================================
    # Stop — job berjalan diselesaikan lebih dulu, lalu cleanup
    # ============================================================

    def stop(self):
        with self._lock:
            if not self.running:
                return {
                    "success": False,
                    "message": "Tidak ada upload yang berjalan.",
                }

            # Worker memeriksa stop_requested sebelum job berikutnya &
            # membersihkan browser di finally.
            self.stop_requested = True
            self.add_log("[INFO] Stop requested", "warning")
            return {
                "success": True,
                "message": "Stop requested. Job berjalan akan diselesaikan, lalu browser ditutup.",
            }

    # ============================================================
    # Status
    # ============================================================

    def status(self):
        total = self.total_jobs_count
        remaining = len(self.jobs)
        done = total - remaining
        progress_persen = round((done / total) * 100) if total > 0 else 0

        current_job = None
        if self.current_schedule_data:
            data = self.current_schedule_data
            product = data.get("product") or {}
            fb = data.get("facebook_schedule") or {}
            files = data.get("files") or {}
            current_job = {
                "video_name": files.get("video", ""),
                "product_title": product.get("title", ""),
                "facebook_schedule": fb.get("datetime", ""),
            }

        return {
            "running": self.running,
            "progress": self.progress,
            "total_job": remaining,
            "logs": self.logs,
            "validation_logs": self.validation_logs,
            "stop_requested": self.stop_requested,
            "info": {
                "total_jobs": total,
                "success_count": self.success_count,
                "failed_count": self.failed_count,
                "current_job": current_job,
                "current_job_index": self.current_job_index,
                "progress_persen": progress_persen,
            },
        }


# Singleton instance (pola sama seperti upload_manager.manager)
facebook_manager = FacebookUploadManager()
