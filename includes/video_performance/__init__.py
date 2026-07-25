"""
Video Performance Module.

Module untuk melakukan scan profil TikTok, sinkronisasi database,
dan matching dengan upload_jobs.

Arsitektur baru:
- Source of Truth adalah akun TikTok, bukan upload_jobs
- Video disimpan sebagai database histori performa video TikTok
- Matching ke upload_jobs hanya sebagai relasi opsional

Folder ini berisi:
    manager.py   - VideoPerformanceManager (background job manager)
    scanner.py   - TikTokProfile wrapper (hanya memanggil library)
    matching.py  - Matching Engine (dipertahankan untuk backward compatibility)
    service.py   - Orchestration layer (mengkoordinasikan alur bisnis baru)
"""
from .manager import VideoPerformanceManager, manager
from .scanner import VideoPerformanceScanner
from .service import VideoPerformanceService

# =============================
# Wire up: Manager -> Service -> Scanner
# =============================
_scanner = VideoPerformanceScanner()
_service = VideoPerformanceService(
    manager=manager,
    scanner=_scanner,
)
manager.set_service(_service)

__all__ = [
    "VideoPerformanceManager",
    "manager",
    "VideoPerformanceScanner",
    "_scanner",
    "VideoPerformanceService",
    "_service",
]

