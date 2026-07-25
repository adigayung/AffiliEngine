"""
tiktok_scrape_videos — Scrape TikTok profile dengan data lengkap.

Pendekatan:
  1. CDP inject interceptor SEBELUM navigasi (tangkap API dari awal)
  2. DOM capture untuk urutan asli TikTok (pinned video first)
  3. Gabung data API + DOM untuk hasil sempurna

Usage:
    from tiktok_scrape_videos import TikTokScraper
    
    scraper = TikTokScraper("salehot0", max_videos=20)
    scraper.run()
"""

from .scraper import TikTokScraper

__all__ = ["TikTokScraper"]
