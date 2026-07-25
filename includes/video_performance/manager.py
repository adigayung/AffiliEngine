"""
VideoPerformanceManager - Background Job Manager.

Mengikuti pattern UploadManager.
Bertanggung jawab mengelola lifecycle scan:
- running state
- progress
- logs
- stop request
- background thread execution
"""

import threading
from datetime import datetime


class VideoPerformanceManager:

    STATE_RUNNING = "running"
    STATE_WAITING_CAPTCHA = "waiting_captcha"
    STATE_COMPLETED = "completed"
    STATE_FAILED = "failed"

    def __init__(self):
        self.state = self.STATE_RUNNING
        self.running = False
        self.progress = 0
        self.logs = []
        self.creator_id = None
        self.stop_requested = False
        self._thread = None
        self._service = None
        print("VideoPerformanceManager Created")

    def set_service(self, service):
        """Set service instance untuk background execution."""
        self._service = service

    def start(self, creator_id: int) -> dict:
        """
        Mulai scan untuk creator tertentu.
        Jika sudah running, return error.
        """
        if self.running:
            return {
                "success": False,
                "message": "Scan sedang berjalan. Tunggu hingga selesai."
            }

        if not self._service:
            return {
                "success": False,
                "message": "Service belum dikonfigurasi."
            }

        self.state = self.STATE_RUNNING
        self.running = True
        self.progress = 0
        self.creator_id = creator_id
        self.stop_requested = False
        self.logs.clear()
        self.add_log(
            f"Scan dimulai untuk creator ID: {creator_id}",
            "info"
        )

        # Jalankan service di background thread
        self._thread = threading.Thread(
            target=self._run_scan_thread,
            args=(creator_id,),
            daemon=True,
        )
        self._thread.start()
        return {
            "success": True,
            "message": "Scan dimulai."
        }

    def _run_scan_thread(self, creator_id: int):
        """
        Jalankan scan di thread terpisah.
        """
        try:
            success = self._service.run_scan(creator_id)
            if not success and self.running:
                self.error("Scan gagal tanpa pesan error.")
        except Exception as e:
            self.error(f"Scan error: {e}")

    def stop(self) -> dict:
        """
        Hentikan scan.
        """
        if not self.running:
            return {
                "success": False,
                "message": "Tidak ada scan yang berjalan."
            }

        self.request_stop()

        self.add_log(
            "Stop diminta oleh pengguna.",
            "warning"
        )

        return {
            "success": True
        }

    def waiting_captcha(self):
        """
        Set status ke waiting_captcha.
        Scan berhenti sementara menunggu user menyelesaikan CAPTCHA.
        """
        self.state = self.STATE_WAITING_CAPTCHA

    def captcha_resolved(self):
        """
        Set status kembali ke running setelah CAPTCHA selesai.
        """
        self.state = self.STATE_RUNNING

    def request_stop(self):
        self.stop_requested = True

    def finish(self):
        """
        Selesaikan scan.
        """
        self.state = self.STATE_COMPLETED
        self.running = False
        self.progress = 100

        self.add_log(
            "Scan selesai.",
            "success"
        )

    def error(self, message: str):
        """
        Tangani error.
        """
        self.state = self.STATE_FAILED
        self.running = False
        self.creator_id = None

        self.add_log(
            message,
            "danger"
        )

    def set_progress(self, value: int):
        self.progress = value

    def add_log(self, text: str, level: str = "info"):
        """
        Tambahkan log dengan format HTML.
        """
        now = datetime.now().strftime("%H:%M:%S")

        colors = {
            "info": "#4dabf7",
            "success": "#51cf66",
            "warning": "#fcc419",
            "danger": "#ff6b6b"
        }

        icons = {
            "info": "\U0001f5c8\ufe0f",
            "success": "\u2705",
            "warning": "\u26a0\ufe0f",
            "danger": "\u274c"
        }

        color = colors.get(level, "#ffffff")
        icon = icons.get(level, "\u2022")

        html = f"""
        <div style="line-height:1.25">
            <span style="color:#666">[{now}]</span>
            <span style="color:{color}">{icon}</span>
            <span>{text}</span>
        </div>
        """

        self.logs.append(html)

        if len(self.logs) > 300:
            self.logs = self.logs[-300:]

        print(f"[{now}] {text}")

    def status(self) -> dict:
        """
        Kembalikan status saat ini.
        """
        return {
            "state": self.state,
            "running": self.running,
            "progress": self.progress,
            "creator_id": self.creator_id,
            "logs": self.logs,
        }


# Singleton instance
manager = VideoPerformanceManager()

