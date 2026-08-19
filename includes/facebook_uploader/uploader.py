"""
uploader.py — Orchestration layer (FacebookUploader) + data loading helpers.

Merangkai seluruh alur yang SUDAH TERBUKTI dari main.py golden version
tanpa menulis ulang logic. Browser lifecycle aman (open/close via browser.py).
"""

import json
from pathlib import Path

from includes.facebook_uploader.browser import (
    DEFAULT_PROFILE_PATH,
    close_browser,
    open_browser,
)

from . import affiliate, flow, scheduling
from .exceptions import FacebookUploaderError

FB_REELS_URL = "https://www.facebook.com/Kawaiii.Ai.Chan/reels"

# Field wajib untuk schedule.json (path bertingkat dipisahkan titik).
REQUIRED_FIELDS = [
    "job_id",
    "creator.username",
    "product.title",
    "product.url",
    "product.shopee_affiliate_link",
    "facebook_schedule.datetime",
    "facebook_schedule.status",
    "content.caption",
    "files.video",
]

_MISSING = object()

STAGE_SCHEDULED = "scheduled"


def get_field(data, dotted_path):
    """
    Ambil nilai dari dict bertingkat 'parent.child'.

    Mengembalikan _MISSING jika key atau parent path tidak ada,
    sehingga nilai legit 0 / "" / False tetap dianggap ADA.
    """
    value = data
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def load_schedule(schedule_path):
    """
    Baca + parse schedule.json. Return raw dict (READ-ONLY, tidak pernah menulis).

    Memisahkan data loading dari alur upload agar Affiliate Engine dapat
    menyuplai schedule_data dari DB / job engine tanpa file JSON baru.
    """
    p = Path(schedule_path)
    if not p.is_file():
        raise FacebookUploaderError(f"schedule.json not found: {p}")
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise FacebookUploaderError(f"Invalid JSON in: {p}\nDetail: {exc}")
    except OSError as exc:
        raise FacebookUploaderError(f"Cannot read schedule.json: {p}\nDetail: {exc}")
    return data


def validate_schedule_data(data):
    """
    Validasi struktur JSON minimal (field wajib) + status facebook_schedule.

    Return: fb_status ('pending' | 'success').
    Raise FacebookUploaderError bila field hilang / status tidak valid.
    """
    for field in REQUIRED_FIELDS:
        if get_field(data, field) is _MISSING:
            raise FacebookUploaderError(f"Required field missing: {field}")
    fb_status = get_field(data, "facebook_schedule.status")
    if fb_status == "success":
        return fb_status
    if fb_status != "pending":
        raise FacebookUploaderError(
            "Invalid facebook_schedule.status: "
            f"Expected 'pending' or 'success', got: {fb_status!r}"
        )
    return fb_status


def build_job_data(data, job_dir):
    """
    Resolve file video LANGSUNG di folder job + bangun dict job untuk flow.

    Return: dict dengan key video_path, caption, affiliate_link,
            facebook_schedule, dll.
    Raise FacebookUploaderError bila video tidak valid.
    """
    job_dir = Path(job_dir)
    video_name = get_field(data, "files.video")
    if video_name is _MISSING:
        raise FacebookUploaderError("files.video is missing from schedule.json")
    video_path = job_dir / video_name
    if Path(video_path).parent.resolve() != job_dir.resolve():
        raise FacebookUploaderError(
            "Video file must be located directly inside the job folder"
        )
    if not Path(video_path).is_file():
        raise FacebookUploaderError(f"Video file not found: {video_path}")
    return {
        "job_id": get_field(data, "job_id"),
        "creator_username": get_field(data, "creator.username"),
        "product_title": get_field(data, "product.title"),
        "product_url": get_field(data, "product.url"),
        "affiliate_link": get_field(data, "product.shopee_affiliate_link"),
        "caption": get_field(data, "content.caption"),
        "video_name": video_name,
        "video_path": str(video_path),
        "facebook_schedule": get_field(data, "facebook_schedule.datetime"),
    }


class FacebookUploader:
    """
    Orchestration layer untuk alur upload + affiliate + scheduling reel.

    Contoh pemakaian dari Affiliate Engine:

        from includes.facebook_uploader import FacebookUploader

        job_data = {
            "video_path": "/path/to/video.mp4",
            "caption": "caption...",
            "affiliate_link": "https://s.shopee.co.id/...",
            "facebook_schedule": "2026-08-20 11:00:00",
        }
        uploader = FacebookUploader()
        result = uploader.run(job_data)
        if result["success"]:
            print(result["message"])

    Bila driver disuplai dari luar (driver=...), browser lifecycle tetap di
    tangan pemanggil. Bila tidak, uploader membuka dan menutup browser sendiri
    dengan aman (tidak ada proses Chrome tertinggal).
    """

    def __init__(self, driver=None, profile_path=DEFAULT_PROFILE_PATH, url=FB_REELS_URL):
        self.driver = driver
        self.profile_path = profile_path
        self.url = url
        self._stage = "browser"

    def run(self, job_data):
        """
        Jalankan full flow. Return dict terstruktur:

            sukses: {"success": True, "stage": "scheduled",
                     "message": "Facebook reel scheduled successfully"}
            gagal : {"success": False, "stage": "<tahap>",
                     "error": "<pesan>", "error_type": "<class>"}
        """
        owns_browser = self.driver is None

        if owns_browser:
            print("[INFO] Opening Facebook Reels:")
            print(self.url)

        try:
            if owns_browser:
                self.driver = open_browser(
                    profile_path=self.profile_path,
                    url=self.url,
                )
                print("[INFO] Facebook Reels page opened successfully")
            return self._run_flow(job_data)
        except Exception as exc:
            return {
                "success": False,
                "stage": self._stage,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
        finally:
            if owns_browser and self.driver is not None:
                print("[INFO] Closing Selenium...")
                close_browser(self.driver)
                self.driver = None
                print("[INFO] Browser closed")

    def _run_flow(self, job_data):
        """Alur penuh — urutan SAMA dengan main.py golden version."""
        video_path = job_data["video_path"]
        caption = job_data["caption"]
        affiliate_link = job_data["affiliate_link"]
        sched_str = job_data["facebook_schedule"]

        driver = self.driver

        # --- Cari tombol "Create reel" + upload UI + file input ---
        self._stage = "create_reel"
        file_input = flow.create_reel(driver)

        # --- Upload video ---
        self._stage = "upload"
        flow.upload_video(driver, file_input, video_path)

        # --- Tunggu "Your reel is safe to publish!" ---
        self._stage = "safe_publish"
        flow.wait_safe_publish(driver)

        # --- Next 1 + Edit reel ---
        self._stage = "first_next"
        flow.click_first_next(driver)
        self._stage = "edit_step"
        flow.wait_edit_step(driver)

        # --- Next 2 + caption ---
        self._stage = "second_next"
        flow.click_second_next(driver)
        self._stage = "caption_box"
        flow.wait_caption_box(driver)
        self._stage = "caption"
        flow.fill_caption(driver, caption)

        # --- Add AI label ---
        self._stage = "ai_label"
        affiliate.check_ai_label(driver)

        # --- Add product + dialog affiliate ---
        self._stage = "add_product"
        affiliate.click_add_product(driver)
        self._stage = "affiliate_dialog"
        affiliate.wait_affiliate_dialog(driver)

        # --- Isi URL + Link name ---
        self._stage = "affiliate_fields"
        affiliate.fill_affiliate_fields(driver, affiliate_link)

        # --- Save affiliate + verifikasi (wrong_save detection) ---
        self._stage = "affiliate_save"
        affiliate.verify_affiliate_save(driver, affiliate_link)

        # --- Scheduling ---
        self._stage = "scheduling"
        scheduling.run_scheduling(driver, sched_str)

        return {
            "success": True,
            "stage": STAGE_SCHEDULED,
            "message": "Facebook reel scheduled successfully",
        }
