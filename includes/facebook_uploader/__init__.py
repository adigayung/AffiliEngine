"""
facebook_uploader — Refactored Facebook Reel Uploader (untuk Affiliate Engine).

Membungkus alur upload + affiliate + scheduling reel Facebook yang SUDAH
TERBUKTI dari main.py golden version ke dalam modul terstruktur tanpa
mengubah behavior, selector, atau explicit wait.

Pemakaian singkat dari Affiliate Engine:

    from includes.facebook_uploader import FacebookUploader

    job_data = {
        "video_path": "/path/to/video.mp4",
        "caption": "caption...",
        "affiliate_link": "https://s.shopee.co.id/...",
        "facebook_schedule": "2026-08-20 11:00:00",
    }
    uploader = FacebookUploader()          # membuka browser sendiri (dan menutupnya)
    result = uploader.run(job_data)
    if result["success"]:
        print(result["message"])

Untuk kompatibilitas dengan schedule.json existing:

    from includes.facebook_uploader import load_schedule, validate_schedule_data, build_job_data

    data = load_schedule(".../schedule.json")          # read-only
    validate_schedule_data(data)
    job_data = build_job_data(data, job_dir)
    result = FacebookUploader().run(job_data)

Bila ingin memakai driver yang sudah ada (tidak ditutup otomatis):

    uploader = FacebookUploader(driver=driver)

Exception khusus (bila ingin menangani langsung, selain result dict):
    FacebookUploaderError, AffiliateSaveError, WrongSaveError, SchedulingError
"""

from .exceptions import (
    AffiliateSaveError,
    FacebookUploaderError,
    SchedulingError,
    WrongSaveError,
)
from .uploader import (
    FacebookUploader,
    build_job_data,
    load_schedule,
    validate_schedule_data,
)

__all__ = [
    "FacebookUploader",
    "load_schedule",
    "validate_schedule_data",
    "build_job_data",
    "FacebookUploaderError",
    "AffiliateSaveError",
    "WrongSaveError",
    "SchedulingError",
]
