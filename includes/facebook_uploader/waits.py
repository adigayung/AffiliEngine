"""
waits.py — Helper explicit wait / polling Selenium.

Dipindahkan PERSIS dari main.py golden version.
WebDriverWait tidak diganti dengan sleep; polling internal dipertahankan.
"""

import time

from .selectors import (
    XPATH_FINAL_SCHEDULE,
    XPATH_SCHED_DLG,
    XPATH_VIDEO_INPUT,
    _DATE_VALUE_RE,
    _PLACEHOLDER_PREVIEW,
    _TIME_VALUE_RE,
    _UPLOAD_KEYWORDS,
)


def _selenium_imports():
    """Import Selenium helpers. Dipanggil saat tahap browser berjalan."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    return By, WebDriverWait, EC


def _selenium_keys():
    from selenium.webdriver.common.keys import Keys
    return Keys


# --- Locator & klik berbasis text / accessible attribute ---

def _wait_text_element(driver, xpath, timeout, label):
    """Tunggu elemen berdasarkan locator text/semantic. Raise TimeoutError(label)."""
    By, WebDriverWait, EC = _selenium_imports()
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
    except Exception:
        raise TimeoutError(label)


def _clickable_ancestor(driver, el):
    """
    Cari elemen clickable terdekat (button / a / role=button / role=link).
    Jika tidak ada, pakai elemen itu sendiri.
    """
    By, _, _ = _selenium_imports()
    try:
        return el.find_element(
            By.XPATH,
            "./ancestor-or-self::*"
            "[self::button or self::a or @role='button' or @role='link'][1]",
        )
    except Exception:
        return el


def _click_element(driver, el):
    """Klik element; fallback ke JS click jika native click gagal."""
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].click();", el)


def _click_text(driver, xpath, timeout, label):
    """Temukan elemen text lalu klik elemen clickable terdekat."""
    el = _wait_text_element(driver, xpath, timeout, label)
    target = _clickable_ancestor(driver, el)
    _click_element(driver, target)


def _wait_visible(driver, xpath, timeout, label):
    """
    Tunggu elemen yang benar-benar visible (is_displayed() == True).

    Penting: beberapa elemen (mis. 'Schedule for later', 'Schedule') punya
    versi tersembunyi di dalam form utama; versi itulah yang harus dihindari.
    """
    By, _, _ = _selenium_imports()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            for el in driver.find_elements(By.XPATH, xpath):
                if el.is_displayed():
                    return el
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError(label)


# --- Upload interface & video ---

def _is_upload_interface(driver):
    """Deteksi UI upload muncul (tanpa menyentuh file input)."""
    try:
        url = driver.current_url.lower()
        if "reel/create" in url or "reels/create" in url:
            return True
    except Exception:
        pass

    try:
        By, _, _ = _selenium_imports()
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        for kw in _UPLOAD_KEYWORDS:
            if kw in body_text:
                return True
    except Exception:
        pass

    return False


def _wait_upload_ui(driver, timeout=30):
    """Tunggu sampai UI upload terdeteksi."""
    _, WebDriverWait, _ = _selenium_imports()
    WebDriverWait(driver, timeout).until(lambda d: _is_upload_interface(d))


def _find_video_input(driver, timeout=30):
    """Cari input[type='file'][accept*=video]."""
    By, WebDriverWait, EC = _selenium_imports()
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, XPATH_VIDEO_INPUT))
    )


def _placeholder_present(driver):
    """True jika teks placeholder preview (state kosong) ada di halaman."""
    By, _, _ = _selenium_imports()
    try:
        body = driver.find_element(By.TAG_NAME, "body").text.lower()
        return _PLACEHOLDER_PREVIEW in body
    except Exception:
        return False


def _wait_upload_state(driver, timeout=90, placeholder_was_present=True):
    """
    Tunggu sampai Facebook menerima video (state upload berubah).

    Signal:
      A) Elemen <video> dengan src/currentSrc muncul.
      B) Teks placeholder 'Upload your video in order to see a preview here'
         ADA sebelum upload lalu HILANG.

    placeholder_was_present diambil SEBELUM send_keys (anti race).
    """
    By, _, _ = _selenium_imports()

    deadline = time.time() + timeout
    while time.time() < deadline:
        # Signal A: video element memuat sumber.
        try:
            for v in driver.find_elements(By.TAG_NAME, "video"):
                if v.get_attribute("src") or v.get_attribute("currentSrc"):
                    return
        except Exception:
            pass

        # Signal B: placeholder ada sebelum upload lalu hilang.
        if placeholder_was_present:
            try:
                body = driver.find_element(By.TAG_NAME, "body").text.lower()
                if _PLACEHOLDER_PREVIEW not in body:
                    return
            except Exception:
                pass

        time.sleep(1)

    raise TimeoutError("Video upload state was not detected")


# --- Scheduling: wait helpers ---

def _wait_sched_dialog_visible(driver, timeout=30):
    """
    Tunggu dialog Scheduling options terbuka.
    Indikator: tombol 'Schedule for later' yang benar-benar visible.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            By, _, _ = _selenium_imports()
            for el in driver.find_elements(By.XPATH, "//*[@aria-label='Schedule for later']"):
                if el.is_displayed():
                    return
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError("Scheduling options dialog did not appear")


def _wait_sched_dialog_closed(driver, timeout=30):
    """
    Tunggu dialog Scheduling options tertutup.
    Indikator: TIDAK ada lagi tombol 'Schedule for later' yang visible
    (elemen tersembunyi di form utama tidak dihitung).
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            By, _, _ = _selenium_imports()
            vis = [
                el
                for el in driver.find_elements(By.XPATH, "//*[@aria-label='Schedule for later']")
                if el.is_displayed()
            ]
            if not vis:
                return
        except Exception:
            return
        time.sleep(1)
    raise TimeoutError("Scheduling options dialog did not close")


def _find_sched_text_inputs(driver):
    """Semua input[type='text'] di dalam dialog Scheduling options."""
    By, _, _ = _selenium_imports()
    return driver.find_elements(By.XPATH, XPATH_SCHED_DLG + "//input[@type='text']")


def _wait_sched_date_input(driver, timeout=30):
    """Cari input Date via pola value (mis. '20 Aug 2026'), bukan index DOM."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for el in _find_sched_text_inputs(driver):
            v = (el.get_attribute("value") or "").strip()
            if _DATE_VALUE_RE.match(v) and el.is_displayed():
                return el
        time.sleep(1)
    raise TimeoutError("Date input not found")


def _wait_sched_time_input(driver, timeout=30):
    """Cari input Time via pola value (mis. '11:00'), bukan index DOM."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for el in _find_sched_text_inputs(driver):
            v = (el.get_attribute("value") or "").strip()
            if _TIME_VALUE_RE.match(v) and el.is_displayed():
                return el
        time.sleep(1)
    raise TimeoutError("Time input not found")


def _wait_schedule_finish(driver, timeout=60):
    """
    Tunggu indikasi proses scheduling selesai:
      - dialog utama (form reel) sudah tidak tampil, ATAU
      - muncul teks 'scheduled' di halaman, ATAU
      - tombol final 'Schedule' tidak lagi tampil (state berubah).
    """
    By, _, _ = _selenium_imports()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            dialogs = driver.find_elements(By.XPATH, "//*[@role='dialog']")
            vis = [d for d in dialogs if d.is_displayed()]
            if not vis:
                return True
        except Exception:
            pass
        try:
            body = driver.find_element(By.TAG_NAME, "body").text.lower()
            if "scheduled" in body:
                return True
        except Exception:
            pass
        try:
            any_displayed = any(
                el.is_displayed()
                for el in driver.find_elements(By.XPATH, XPATH_FINAL_SCHEDULE)
            )
            if not any_displayed:
                return True
        except Exception:
            # Elemen final Schedule hilang -> state sudah berubah.
            return True
        time.sleep(1)
    return False
