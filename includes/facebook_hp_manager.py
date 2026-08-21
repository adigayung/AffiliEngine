# File : includes\facebook_hp_manager.py
"""
facebook_hp_manager.py — Manager antrian job Facebook HP (Android).

TERISOLASI dari TikTok:
  - TIDAK memakai upload_jobs / schedule_batches (MySQL TikTok).
  - TIDAK memakai schedule.status TikTok sebagai syarat queue.
  - Hanya validasi facebook_paths.validate_facebook_path (READ-ONLY):
        status == "valid"  -> masuk queue (facebook_schedule.status == "pending")
        status == "completed" -> SKIP (sudah success, jangan upload ulang)
        status == "invalid"   -> SKIP
  - Tidak spawn thread worker. Konsumen (WebSocket / test) menarik job
    satu per satu via get_next_job() -> runner -> complete_job_*.

Pola queue mengikuti UploadManager (TikTok) dan FacebookUploadManager (PC),
tetapi tanpa dependency MySQL / Selenium.
"""

import json
import os
import threading
from datetime import datetime

from includes.facebook_paths import validate_facebook_path


class FacebookHpManager:

    def __init__(self):
        # --- Queue / state runtime ---
        self.running = False
        self.stop_requested = False
        self.progress = 0
        self.jobs = []                     # list project path (hanya VALID/pending)

        # --- Info job saat ini ---
        self.current_job_path = None
        self.current_schedule_data = None
        self.current_job_index = 0

        # --- Statistik ---
        self.total_jobs_count = 0
        self.success_count = 0
        self.failed_count = 0

        # --- Log ---
        self.logs = []
        self.validation_logs = []

        self._lock = threading.Lock()
        print("FacebookHpManager Created")

    # ============================================================
    # Log — pola HTML sama dengan manager existing
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
        """Simpan log validasi dari start() (list of (level, text))."""
        self.validation_logs.clear()
        for level, text in details:
            self.add_validation_log(text, level)

    # ============================================================
    # Start — bangun queue (READ-ONLY terhadap schedule.json)
    # ============================================================

    def start(self, path_list):
        """
        Bangun queue Facebook HP dari daftar project path.

        Args:
            path_list: str (teks area, satu path per baris) ATAU list[str].

        Returns:
            dict: {"success": bool, "total_job": int, "message": str}
        """
        with self._lock:
            if self.running:
                return {
                    "success": False,
                    "message": "Queue Facebook HP masih berjalan.",
                }

            if isinstance(path_list, str):
                raw_paths = path_list.splitlines()
            else:
                raw_paths = list(path_list or [])

            self.jobs.clear()
            self.stop_requested = False
            self.logs.clear()
            self.validation_logs.clear()

            seen = set()
            for line in raw_paths:
                path = str(line or "").strip()
                if not path or path in seen:
                    continue
                seen.add(path)

                result = validate_facebook_path(path)
                name = result["video_name"] or os.path.basename(path.rstrip("\\/")) or path

                if result["status"] == "valid":
                    self.jobs.append(path)
                    self.add_validation_log(f"[VALID] {name}", "valid")
                    self.add_validation_log(
                        f"    Facebook schedule: {result['facebook_datetime']}", "info"
                    )
                elif result["status"] == "completed":
                    self.add_validation_log(
                        f"[COMPLETED] {name} — {result['reason']}", "completed"
                    )
                else:
                    self.add_validation_log(
                        f"[SKIP] {name} — {result['reason']}", "skip"
                    )

            if not self.jobs:
                self.add_log(
                    "[INFO] Tidak ada project Facebook HP yang valid (status pending).",
                    "info",
                )
                return {
                    "success": False,
                    "total_job": 0,
                    "message": "Tidak ada project valid. Periksa log validasi.",
                }

            self.running = True
            self.progress = 0
            self.total_jobs_count = len(self.jobs)
            self.success_count = 0
            self.failed_count = 0
            self.current_job_path = None
            self.current_schedule_data = None
            self.current_job_index = 0

            self.add_log(
                f"[INFO] Queue Facebook HP dibuat: {len(self.jobs)} job siap diproses.",
                "success",
            )

            return {
                "success": True,
                "total_job": len(self.jobs),
            }

    # ============================================================
    # Konsumen WebSocket mengambil 1 job
    # ============================================================

    def get_next_job(self):
        """
        Ambil job berikutnya dari queue. Dipanggil oleh konsumen WebSocket
        (Phase 3) atau oleh test (Phase 2).

        Returns:
            str | None: project path, atau None bila tidak running / kosong.
        """
        with self._lock:
            if not self.running:
                return None
            if len(self.jobs) == 0:
                return None

            self.current_job_path = self.jobs[0]
            self.current_job_index += 1

            # Baca schedule.json untuk current job (informasional)
            schedule_path = os.path.join(self.current_job_path, "schedule.json")
            if os.path.exists(schedule_path):
                try:
                    with open(schedule_path, "r", encoding="utf-8") as f:
                        self.current_schedule_data = json.load(f)
                except Exception:
                    self.current_schedule_data = None
            else:
                self.current_schedule_data = None

            return self.current_job_path

    # ============================================================
    # Job selesai -> lanjut job berikutnya
    # ============================================================

    def complete_job_success(self):
        """Job selesai SUKSES (persistence success sudah terverifikasi runner)."""
        with self._lock:
            if self.jobs:
                self.jobs.pop(0)
                self.success_count += 1

            self.progress = 0
            self.current_job_path = None
            self.current_schedule_data = None

            if len(self.jobs) == 0:
                self.finish()

    def complete_job_failed(self):
        """Job GAGAL (command gagal / persistence gagal). Status tetap pending."""
        with self._lock:
            if self.jobs:
                self.jobs.pop(0)
                self.failed_count += 1

            self.progress = 0
            self.current_job_path = None
            self.current_schedule_data = None

            if len(self.jobs) == 0:
                self.finish()

    # ============================================================
    # Stop
    # ============================================================

    def request_stop(self):
        self.stop_requested = True

    def stop(self):
        """
        Stop queue Facebook HP.

        Job yang sedang berjalan tetap diselesaikan oleh konsumen WebSocket
        (loop `while manager.running` berhenti SETELAH job tersebut selesai),
        sedangkan SISA queue langsung dibatalkan di sini.

        Konsumen WebSocket memeriksa `self.running` di tiap iterasi loop —
        karena stop() men-set running=False, loop akan berhenti setelah job
        berjalan selesai dan memanggil complete_job_*.
        """
        with self._lock:
            if not self.running:
                return {
                    "success": False,
                    "message": "Tidak ada queue Facebook HP yang berjalan.",
                }
            self.stop_requested = True
            remaining = len(self.jobs)
            self.jobs.clear()
            self.running = False
            self.progress = 100
            self.current_job_path = None
            self.current_schedule_data = None
            self.add_log(
                f"Stop diminta oleh pengguna — {remaining} job tertunda dibatalkan.",
                "warning",
            )
            return {
                "success": True,
                "message": "Stop diminta. Job berjalan diselesaikan, sisa queue dibatalkan.",
            }

    # ============================================================
    # Semua job selesai
    # ============================================================

    def finish(self):
        self.running = False
        self.progress = 100
        self.current_job_path = None
        self.current_schedule_data = None
        if self.stop_requested:
            self.add_log("Queue Facebook HP dihentikan oleh pengguna.", "warning")
        else:
            self.add_log("Semua job Facebook HP telah selesai.", "success")

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


# Singleton (pola sama seperti manager/facebook_manager).
facebook_hp_manager = FacebookHpManager()
