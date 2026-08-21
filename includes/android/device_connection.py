# File : includes\android\device_connection.py
"""
device_connection.py — Registry status koneksi Android (WebSocket).

Mencatat kapan aplikasi Android (Kotlin) terhubung / terputus dari server
melalui WebSocket. Bersifat OBSERVASI murni:
  - TIDAK mengubah command protocol (click, input_text, push_file, dll).
  - TIDAK mengubah executor Kotlin.
  - TIDAK ikut campur dalam loop eksekusi job TikTok.

Informasi ini nantinya bisa dipakai oleh endpoint status (misalnya
/upload_video/facebook/status) untuk menampilkan:
  - Android connected
  - Android disconnected
  - detail koneksi (endpoint, platform, waktu koneksi)

Thread-safe karena setiap koneksi WebSocket berjalan di thread berbeda.
"""

import threading
import uuid
from datetime import datetime


class AndroidConnectionRegistry:

    def __init__(self):
        self._lock = threading.Lock()
        self._connections = {}           # token -> dict detail koneksi
        self._last_disconnect_at = None  # datetime disconnect terakhir

    # =====================================================
    # Register / Unregister
    # =====================================================

    def register(self, endpoint, platform=None):
        """Catat koneksi Android baru.

        Args:
            endpoint: path WebSocket yang dipakai
                      (mis. "/service/video_uploader").
            platform: identitas platform bila diperlukan
                      (default None — arsitektur existing tidak
                      membutuhkan platform assignment).

        Returns:
            str: token unik untuk koneksi ini (dipakai saat unregister).
        """
        token = uuid.uuid4().hex
        now = datetime.now()

        with self._lock:
            self._connections[token] = {
                "token": token,
                "endpoint": endpoint,
                "platform": platform,
                "connected_at": now,
            }

        print(
            f"[DeviceConnection] Android connected "
            f"(token={token}, endpoint={endpoint}, platform={platform})"
        )

        return token

    def unregister(self, token):
        """Hapus catatan koneksi (dipanggil saat WebSocket ditutup).

        Returns:
            bool: True bila token ditemukan dan dihapus.
        """
        with self._lock:
            if token in self._connections:
                del self._connections[token]
                self._last_disconnect_at = datetime.now()
                removed = True
            else:
                removed = False

        if removed:
            print(
                f"[DeviceConnection] Android disconnected (token={token})"
            )

        return removed

    # =====================================================
    # Query Status
    # =====================================================

    def is_connected(self):
        """True bila ada minimal satu koneksi Android aktif."""
        with self._lock:
            return len(self._connections) > 0

    def connection_count(self):
        """Jumlah koneksi Android aktif saat ini."""
        with self._lock:
            return len(self._connections)

    def status(self):
        """Snapshot status koneksi untuk konsumsi endpoint status (UI)."""
        with self._lock:
            connections = [
                {
                    "token": c["token"],
                    "endpoint": c["endpoint"],
                    "platform": c["platform"],
                    "connected_at": c["connected_at"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
                for c in self._connections.values()
            ]

            return {
                "connected": len(connections) > 0,
                "connection_count": len(connections),
                "connections": connections,
                "last_disconnect_at": (
                    self._last_disconnect_at.strftime("%Y-%m-%d %H:%M:%S")
                    if self._last_disconnect_at is not None
                    else None
                ),
            }


# Singleton global (pola sama seperti manager singleton di modul lain).
device_connection = AndroidConnectionRegistry()
