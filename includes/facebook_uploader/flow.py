"""
flow.py — Tahap utama reel: create reel, upload video, safe publish,
Next pertama/kedua, caption.

Urutan dan selector IDENTIK dengan main.py golden version.
"""

from .exceptions import FacebookUploaderError
from .pacing import DELAY_MAJOR, DELAY_NORMAL, DELAY_TRANSITION, human_delay
from .selectors import (
    XPATH_CAPTION,
    XPATH_CREATE_REEL,
    XPATH_EDIT_STEP,
    XPATH_NEXT,
    XPATH_SAFE_PUBLISH,
)
from .waits import (
    _click_element,
    _clickable_ancestor,
    _find_video_input,
    _placeholder_present,
    _selenium_imports,
    _selenium_keys,
    _wait_text_element,
    _wait_upload_state,
    _wait_upload_ui,
)


def create_reel(driver):
    """
    Klik "Create reel", tunggu UI upload, lalu temukan input file video.

    Return: file_input (input[type='file'][accept*='video']).
    """
    create_el = None
    try:
        create_el = _wait_text_element(
            driver, XPATH_CREATE_REEL, 30, "Create reel"
        )
    except Exception:
        pass

    if create_el is None:
        By, _, _ = _selenium_imports()
        if not driver.find_elements(By.XPATH, XPATH_CREATE_REEL):
            print("[ERROR] Create reel button not found")
            raise FacebookUploaderError("Create reel button not found")
        print("[ERROR] Timeout waiting for Create reel")
        raise FacebookUploaderError("Timeout waiting for Create reel")
    print("[INFO] Create reel found")

    click_target = _clickable_ancestor(driver, create_el)

    human_delay(DELAY_NORMAL, "before Create reel")
    print("[INFO] Clicking Create reel...")
    try:
        _click_element(driver, click_target)
    except Exception as exc:
        print("[ERROR] Failed to click Create reel:")
        print(repr(exc))
        raise FacebookUploaderError(f"Failed to click Create reel: {exc!r}")
    print("[INFO] Create reel clicked")
    human_delay(DELAY_TRANSITION)

    # --- Tunggu UI upload muncul ---
    try:
        _wait_upload_ui(driver, timeout=30)
    except Exception:
        print("[ERROR] Upload interface was not detected")
        raise FacebookUploaderError("Upload interface was not detected")
    print("[INFO] Upload interface detected")

    # --- Cari input[type='file'][accept*='video'] ---
    file_input = None
    try:
        file_input = _find_video_input(driver, timeout=30)
    except Exception:
        pass

    if file_input is None:
        print("[ERROR] Video file input not found")
        raise FacebookUploaderError("Video file input not found")
    print("[INFO] Video file input found")
    return file_input


def upload_video(driver, file_input, video_path):
    """Upload video dari path job ke composer, lalu tunggu state upload."""
    print("[INFO] Video file:")
    print(str(video_path))
    human_delay(DELAY_NORMAL, "before video upload")
    print("[INFO] Video upload started")

    placeholder_seen = _placeholder_present(driver)

    try:
        file_input.send_keys(str(video_path))
    except Exception as exc:
        print("[ERROR] Failed to upload video:")
        print(repr(exc))
        raise FacebookUploaderError(f"Failed to upload video: {exc!r}")

    try:
        _wait_upload_state(
            driver,
            timeout=90,
            placeholder_was_present=placeholder_seen,
        )
    except Exception:
        print("[ERROR] Video upload state was not detected")
        raise FacebookUploaderError("Video upload state was not detected")

    human_delay(DELAY_MAJOR, "after video upload")


def wait_safe_publish(driver):
    """Tunggu 'Your reel is safe to publish!'."""
    print("[INFO] Waiting for Facebook video processing...")
    try:
        _wait_text_element(
            driver, XPATH_SAFE_PUBLISH, 120, "safe publish"
        )
    except Exception:
        print('[ERROR] "Your reel is safe to publish!" was not detected')
        raise FacebookUploaderError('"Your reel is safe to publish!" was not detected')
    print('[INFO] "Your reel is safe to publish!" detected')


def click_first_next(driver):
    """Next 1 dari layar 'Create reel / Replace Video'."""
    human_delay(DELAY_NORMAL, "before first Next")
    print("[INFO] Clicking first Next...")
    try:
        next1 = _wait_text_element(driver, XPATH_NEXT, 30, "Next 1")
        _click_element(driver, next1)
    except Exception:
        print("[ERROR] First Next button not found")
        raise FacebookUploaderError("First Next button not found")
    print("[INFO] First Next clicked")
    human_delay(DELAY_MAJOR, "after first Next")


def wait_edit_step(driver):
    """Tunggu step 2 ('Edit reel') selesai dimuat."""
    try:
        _wait_text_element(driver, XPATH_EDIT_STEP, 30, "Edit reel step")
    except Exception:
        print("[ERROR] Reel edit step was not detected after first Next")
        raise FacebookUploaderError("Reel edit step was not detected after first Next")
    print("[INFO] Reel edit step detected")


def click_second_next(driver):
    """Next 2 dari layar 'Edit reel' (setting diabaikan)."""
    human_delay(DELAY_NORMAL, "before second Next")
    print("[INFO] Clicking second Next...")
    try:
        next2 = _wait_text_element(driver, XPATH_NEXT, 30, "Next 2")
        _click_element(driver, next2)
    except Exception:
        print("[ERROR] Second Next button not found")
        raise FacebookUploaderError("Second Next button not found")
    print("[INFO] Second Next clicked")


def wait_caption_box(driver):
    """Tunggu textbox caption."""
    try:
        _wait_text_element(driver, XPATH_CAPTION, 30, "caption textbox")
    except Exception:
        print("[ERROR] Caption textbox not found")
        raise FacebookUploaderError("Caption textbox not found")
    print("[INFO] Caption textbox detected")


def fill_caption(driver, caption):
    """Isi caption dari schedule.json + verifikasi text yang tampil."""
    print("[INFO] Caption loaded from schedule.json")
    human_delay(DELAY_NORMAL, "before caption")
    try:
        _fill_caption(driver, caption)
    except Exception as exc:
        print("[ERROR] Caption could not be verified")
        print(repr(exc))
        raise FacebookUploaderError(f"Caption could not be verified: {exc!r}")
    print("[INFO] Caption entered successfully")
    human_delay(DELAY_NORMAL, "after caption")


def _fill_caption(driver, caption):
    """Isi caption ke contenteditable role=textbox. Verifikasi text yang tampil."""
    By, _, _ = _selenium_imports()
    Keys = _selenium_keys()

    box = driver.find_element(By.XPATH, XPATH_CAPTION)

    # focus textbox
    try:
        box.click()
    except Exception:
        driver.execute_script("arguments[0].focus();", box)

    # pilih konten existing (jika ada) lalu ketik caption
    box.send_keys(Keys.CONTROL, "a")
    box.send_keys(caption)

    # verifikasi
    shown = ""
    try:
        shown = box.text
    except Exception:
        pass
    if caption not in shown:
        raise RuntimeError("Caption not visible in textbox")
