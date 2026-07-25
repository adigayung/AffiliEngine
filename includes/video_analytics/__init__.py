"""
Video Analytics Module.

Framework untuk menganalisis performa video TikTok.
Modul ini menjadi Service Layer yang menghubungkan Flask dengan
seluruh proses Video Analytics.

Arsitektur:
    Router (Thin Controller)
        ↓
    video_analytics.py  (Service Layer - business logic)
        ↓
    Database (tiktok_videos, tiktok_video_stats)
        ↓
    Template (hanya menampilkan data)

Modul ini TIDAK memiliki ketergantungan dengan:
    - includes.tiktok_scrape_videos
    - Scraping logic
    - Background jobs
    - Scheduler
"""
from .video_analytics import VideoAnalyticsService, video_analytics_service

__all__ = [
    "VideoAnalyticsService",
    "video_analytics_service",
]
