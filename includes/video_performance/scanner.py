"""
VideoPerformanceScanner - Wrapper terhadap TikTokScraper (tiktok_scrape_videos).

Scanner hanya bertanggung jawab:
1. Menerima username
2. Memanggil TikTokScraper.run()
3. Menormalisasi field name (id->video_id, desc->caption, upload_date->upload_time)
4. Mengembalikan list[dict]

Scanner TIDAK BOLEH mengetahui:
- MySQL
- upload_jobs
- matching
- scheduler
- business logic project
"""

import logging
import threading
import time

from includes.tiktok_scrape_videos import TikTokScraper

CAPTCHA_POLL_INTERVAL = 0.5
DRIVER_WAIT_TIMEOUT = 20


class VideoPerformanceScanner:

    def __init__(self, profile_path="./chromium", scroll_count=5, timeout=60, captcha_timeout=300, debug=True):
        self.profile_path = profile_path
        self.scroll_count = scroll_count
        self.timeout = timeout
        self.captcha_timeout = captcha_timeout
        self.debug = debug

    def _normalize_video(self, video):
        return {
            "video_id": video.get("id", ""),
            "caption": video.get("desc", ""),
            "upload_time": video.get("upload_date", ""),
            "upload_timestamp": video.get("upload_timestamp", 0),
            "views": video.get("views", 0) or 0,
            "likes": video.get("likes", 0) or 0,
            "comments": video.get("comments", 0) or 0,
            "shares": video.get("shares", 0) or 0,
            "video_url": video.get("video_url", ""),
            "thumbnail_url": video.get("thumbnail_url", ""),
            "duration_sec": video.get("duration_sec", 0),
        }

    def scan(self, username):
        if not username or not username.strip():
            raise ValueError("Username tidak boleh kosong.")
        username = username.strip()
        scraper = TikTokScraper(
            username=username,
            max_videos=max(20, self.scroll_count * 10),
            profile_path=self.profile_path,
        )
        try:
            raw_videos = scraper.run()
            if not raw_videos:
                return []
            return [self._normalize_video(v) for v in raw_videos]
        except Exception as e:
            raise RuntimeError(f"Scraping gagal untuk @{username}: {e}")

    def scan_with_captcha_awareness(
        self,
        username,
        on_captcha_started=None,
        on_captcha_finished=None,
        on_captcha_timeout=None,
        on_captcha_browser_closed=None,
    ):
        if not username or not username.strip():
            raise ValueError("Username tidak boleh kosong.")
        username = username.strip()
        scraper = TikTokScraper(
            username=username,
            max_videos=max(20, self.scroll_count * 10),
            profile_path=self.profile_path,
        )
        try:
            raw_videos = scraper.run()
            if not raw_videos:
                return []
            return [self._normalize_video(v) for v in raw_videos]
        except Exception as e:
            err_msg = str(e).lower()
            browser_errors = [
                "no such window", "target window already closed",
                "window already closed", "connection refused",
                "cannot find window", "invalid session id",
                "disconnected", "not connected", "unable to connect",
            ]
            if any(x in err_msg for x in browser_errors):
                if on_captcha_browser_closed:
                    on_captcha_browser_closed()
                return []
            raise RuntimeError(f"Scraping gagal untuk @{username}: {e}")


def _is_captcha_detected_static(driver):
    from selenium.webdriver.common.by import By
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, ".captcha-verify-container")
        for el in elements:
            if el.is_displayed():
                return True
    except Exception:
        pass
    try:
        selectors = [
            "iframe[src*='arkoselabs']",
            "iframe[src*='funcaptcha']",
            "iframe[src*='captcha']",
            "iframe[src*='challenge']",
        ]
        for s in selectors:
            try:
                iframes = driver.find_elements(By.CSS_SELECTOR, s)
                for iframe in iframes:
                    if iframe.is_displayed():
                        return True
            except Exception:
                continue
    except Exception:
        pass
    try:
        url = driver.current_url.lower()
        if "/challenge" in url or "/captcha" in url:
            return True
    except Exception:
        pass
    try:
        xpaths = [
            "//*[contains(text(), 'Are you a robot')]",
            "//*[contains(text(), 'Please confirm you are human')]",
        ]
        for xpath in xpaths:
            try:
                els = driver.find_elements(By.XPATH, xpath)
                for el in els:
                    if el.is_displayed():
                        return True
            except Exception:
                continue
    except Exception:
        pass
    return False
