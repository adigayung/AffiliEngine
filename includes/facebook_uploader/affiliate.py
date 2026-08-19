"""
affiliate.py — Add AI label, Add product, dialog affiliate, isi URL,
isi Link name, Save affiliate dengan validasi ketat + wrong_save detection.

BAGIAN PALING KRITIS. Behavior IDENTIK dengan main.py golden version.
"""

import time

from .exceptions import AffiliateSaveError, FacebookUploaderError, WrongSaveError
from .pacing import DELAY_MAJOR, DELAY_MICRO, DELAY_NORMAL, DELAY_TRANSITION, human_delay
from .selectors import (
    XPATH_ADD_PRODUCT,
    XPATH_AFFILIATE_DIALOG,
    XPATH_AI_LABEL,
    XPATH_DIALOG_PRODUCT_LINK,
    XPATH_LINK_NAME_INPUT,
    XPATH_SAVE,
    XPATH_SCHED_OPT,
    XPATH_URL_INPUT,
)
from .waits import (
    _click_element,
    _click_text,
    _selenium_imports,
    _wait_text_element,
)

LINK_NAME_TEXT = "Cobain Mumpung PROMO!"


def check_ai_label(driver):
    """Pastikan 'Add AI label' AKTIF (jika sudah aktif, jangan diklik lagi)."""
    human_delay(DELAY_MICRO)
    print("[INFO] Checking Add AI label...")
    try:
        _ensure_ai_label(driver)
    except Exception:
        print("[ERROR] Add AI label could not be enabled")
        raise FacebookUploaderError("Add AI label could not be enabled")
    print("[INFO] Add AI label is enabled")


def click_add_product(driver):
    """Klik 'Add a product to your reel...'."""
    try:
        _wait_text_element(driver, XPATH_ADD_PRODUCT, 30, "Add product")
    except Exception:
        print("[ERROR] Add product button not found")
        raise FacebookUploaderError("Add product button not found")
    print("[INFO] Add product button found")

    human_delay(DELAY_NORMAL, "before Add product")
    print("[INFO] Add product button clicked")
    try:
        _click_text(driver, XPATH_ADD_PRODUCT, 30, "Add product")
    except Exception:
        print("[ERROR] Add product button not found")
        raise FacebookUploaderError("Add product button not found")
    human_delay(DELAY_TRANSITION)


def wait_affiliate_dialog(driver):
    """Tunggu dialog 'Add affiliate product' terbuka."""
    try:
        _wait_text_element(
            driver, XPATH_AFFILIATE_DIALOG, 30, "affiliate dialog"
        )
    except Exception:
        print("[ERROR] Affiliate product dialog not detected")
        raise AffiliateSaveError("Affiliate product dialog not detected")
    try:
        _wait_text_element(
            driver, XPATH_DIALOG_PRODUCT_LINK, 15, "product link text"
        )
    except Exception:
        print("[ERROR] Affiliate product dialog not detected")
        raise AffiliateSaveError("Affiliate product dialog not detected")
    print("[INFO] Affiliate product dialog detected")


def fill_affiliate_fields(driver, shopee_url):
    """Isi URL Shopee affiliate (dari data job) lalu Link name."""
    human_delay(DELAY_NORMAL, "before affiliate URL")
    try:
        _fill_url_input(driver, shopee_url)
    except Exception:
        print("[ERROR] Shopee affiliate URL input not found")
        raise AffiliateSaveError("Shopee affiliate URL input not found")
    print("[INFO] Shopee affiliate URL entered")

    human_delay(DELAY_MICRO)
    try:
        _fill_link_name(driver, LINK_NAME_TEXT)
    except Exception:
        print("[ERROR] Link name input not found")
        raise AffiliateSaveError("Link name input not found")
    print("[INFO] Link name entered:")
    print(LINK_NAME_TEXT)


def verify_affiliate_save(driver, shopee_url):
    """
    Verifikasi input affiliate (URL + Link name), pilih Save yang BENAR
    (role=button, visible, enabled), lalu verifikasi pasca-Save.

    Jika Save yang salah (publish/draft/Content Library) -> WrongSaveError.
    """
    print("[INFO] Starting affiliate Save verification")

    # 15a. URL input: harus visible + nilainya sesuai schedule.json.
    try:
        url_el = _find_url_input(driver)
    except Exception:
        print("[ERROR] URL input not found")
        raise AffiliateSaveError("URL input not found")
    if not url_el.is_displayed():
        print("[ERROR] URL input not visible")
        raise AffiliateSaveError("URL input not visible")
    print("[INFO] URL input visible")
    url_value = url_el.get_attribute("value")
    if url_value != shopee_url:
        print("[ERROR] URL value mismatch:")
        print("Expected:", shopee_url)
        print("Actual:  ", url_value)
        raise AffiliateSaveError("URL value mismatch")

    # 15b. Link name input: harus visible + nilainya persis.
    try:
        name_el = _find_link_name_input(driver)
    except Exception:
        print("[ERROR] Link name input not found")
        raise AffiliateSaveError("Link name input not found")
    if not name_el.is_displayed():
        print("[ERROR] Link name input not visible")
        raise AffiliateSaveError("Link name input not visible")
    print("[INFO] Link name input visible")
    name_value = name_el.get_attribute("value")
    if name_value != LINK_NAME_TEXT:
        print("[ERROR] Link name value mismatch:")
        print("Expected:", LINK_NAME_TEXT)
        print("Actual:  ", name_value)
        raise AffiliateSaveError("Link name value mismatch")

    # 15c. Pilih Save affiliate yang benar (role=button, visible, enabled).
    print("[INFO] Searching visible Save buttons")
    try:
        save_btn = _wait_save_enabled(driver, timeout=90)
    except Exception:
        print("[ERROR] Affiliate Save button not visible and enabled")
        raise AffiliateSaveError("Affiliate Save button not visible and enabled")

    human_delay(DELAY_NORMAL, "before affiliate Save")
    print("[INFO] Clicking correct affiliate Save")
    try:
        _click_element(driver, save_btn)
    except Exception as exc:
        print("[ERROR] Failed to click affiliate Save")
        print(repr(exc))
        raise AffiliateSaveError(f"Failed to click affiliate Save: {exc!r}")

    # 15d. Verifikasi hasil Save:
    #      dialog affiliate tertutup + kembali ke form utama +
    #      "Scheduling options" visible.
    human_delay(DELAY_MAJOR, "after affiliate Save")
    print("[INFO] Waiting for affiliate dialog to close")
    save_result = _wait_affiliate_save_success(driver, timeout=40)
    if save_result == "wrong_save":
        print("[ERROR] Wrong Save button was clicked")
        print("[ERROR] Main form Save was triggered instead of affiliate Save")
        raise WrongSaveError(
            "Wrong Save button was clicked; "
            "Main form Save was triggered instead of affiliate Save"
        )
    if save_result != "success":
        print("[ERROR] Affiliate Save could not be verified")
        raise AffiliateSaveError("Affiliate Save could not be verified")
    print("[INFO] Affiliate product dialog closed")
    print("[INFO] Returned to reel main form")
    print("[INFO] Scheduling options detected")
    print("[INFO] Affiliate product Save verified successfully")


# --- Add AI label ---

def _ai_label_checked(driver):
    By, _, _ = _selenium_imports()
    try:
        els = driver.find_elements(By.XPATH, XPATH_AI_LABEL)
        if not els:
            return False
        el = els[0]
        aria = el.get_attribute("aria-checked")
        checked = el.get_attribute("checked")
        if aria is not None and str(aria).lower() == "true":
            return True
        if checked is not None:
            return True
    except Exception:
        pass
    return False


def _ensure_ai_label(driver):
    """Pastikan 'Add AI label' AKTIF (jika sudah aktif, jangan klik lagi)."""
    By, _, _ = _selenium_imports()

    el = None
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            el = driver.find_element(By.XPATH, XPATH_AI_LABEL)
            break
        except Exception:
            time.sleep(0.5)
    if el is None:
        raise TimeoutError("Add AI label not found")

    if _ai_label_checked(driver):
        return

    for _ in range(5):
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].click();", el)
        time.sleep(1)
        if _ai_label_checked(driver):
            return

    raise RuntimeError("Add AI label could not be enabled")


# --- Affiliate dialog: URL, Link name, Save ---

def _fill_url_input(driver, url):
    By, _, _ = _selenium_imports()
    els = driver.find_elements(By.XPATH, XPATH_URL_INPUT)
    if not els:
        # fallback berbasis atribut semantic (bukan class).
        els = driver.find_elements(By.XPATH, "//input[@type='text' and @maxlength='400']")
    if not els:
        raise RuntimeError("URL input not found")
    el = els[0]
    try:
        el.clear()
    except Exception:
        pass
    el.send_keys(url)


def _fill_link_name(driver, name):
    By, _, _ = _selenium_imports()
    els = driver.find_elements(By.XPATH, XPATH_LINK_NAME_INPUT)
    if not els:
        # fallback: input text kedua di dalam dialog affiliate.
        els = driver.find_elements(By.XPATH, "//div[@role='dialog']//input[@type='text']")
        if len(els) >= 2:
            els = [els[1]]
        elif els:
            els = [els[0]]
    if not els:
        raise RuntimeError("Link name input not found")
    el = els[0]
    try:
        el.clear()
    except Exception:
        pass
    el.send_keys(name)


def _find_url_input(driver):
    """Temukan input URL affiliate yang sedang visible di dialog affiliate."""
    By, _, _ = _selenium_imports()
    els = driver.find_elements(By.XPATH, XPATH_URL_INPUT)
    if not els:
        els = driver.find_elements(By.XPATH, "//input[@type='text' and @maxlength='400']")
    for el in els:
        if el.is_displayed():
            return el
    if els:
        return els[0]
    raise RuntimeError("URL input not found")


def _find_link_name_input(driver):
    """Temukan input Link name yang sedang visible di dialog affiliate."""
    By, _, _ = _selenium_imports()
    els = driver.find_elements(By.XPATH, XPATH_LINK_NAME_INPUT)
    if not els:
        els = driver.find_elements(By.XPATH, "//div[@role='dialog']//input[@type='text']")
        if len(els) >= 2:
            els = [els[1]]
        elif els:
            els = [els[0]]
    for el in els:
        if el.is_displayed():
            return el
    if els:
        return els[0]
    raise RuntimeError("Link name input not found")


def _wait_save_enabled(driver, timeout=90):
    """
    Pilih tombol Save AFFILIATE yang benar:
      - role='button', aria-label='Save'
      - is_displayed() == True
      - aria-disabled != 'true'

    Save form utama yang tersembunyi di balik overlay/dialog TIDAK dipilih,
    meskipun attribut aria-disabled-nya terlihat enabled, karena filter
    is_displayed() akan menolaknya. Semua kandidat di-log untuk audit.
    """
    By, _, _ = _selenium_imports()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            cands = driver.find_elements(By.XPATH, XPATH_SAVE)
        except Exception:
            cands = []
        chosen = None
        for el in cands:
            try:
                disp = el.is_displayed()
                dis = el.get_attribute("aria-disabled")
            except Exception:
                continue
            if disp and (dis is None or str(dis).lower() != "true"):
                chosen = el
                break
        if chosen is not None:
            # Log semua kandidat Save (audit / deteksi salah klik).
            print("[INFO] Save candidate dump:")
            for idx, el in enumerate(cands):
                try:
                    disp = el.is_displayed()
                    enab = el.is_enabled()
                    dis = el.get_attribute("aria-disabled")
                    loc = el.location
                    size = el.size
                except Exception:
                    continue
                print(
                    f"[INFO] Save candidate {idx}: displayed={disp}, "
                    f"enabled={enab}, aria-disabled={dis}, "
                    f"location={loc}, size={size}"
                )
            return chosen
        time.sleep(1)
    raise TimeoutError("Affiliate Save button not visible and enabled")


def _wait_affiliate_save_success(driver, timeout=40):
    """
    Verifikasi hasil klik Save affiliate.

    Return:
      - "success"    : dialog affiliate tertutup + form utama kembali +
                       "Scheduling options" visible.
      - "wrong_save" : terdeteksi toast publish / halaman pindah ke Content Library.
      - "timeout"    : kondisi sukses tidak tercapai.
    """
    By, _, _ = _selenium_imports()
    deadline = time.time() + timeout
    while time.time() < deadline:
        # Deteksi salah klik -> Save form utama memicu publish/draft.
        try:
            body = driver.find_element(By.TAG_NAME, "body").text.lower()
            if "your post has successfully been shared" in body:
                return "wrong_save"
        except Exception:
            pass
        try:
            if "content_library" in driver.current_url.lower():
                return "wrong_save"
        except Exception:
            pass

        # Dialog affiliate masih terbuka?
        aff_open = False
        try:
            for d in driver.find_elements(By.XPATH, "//*[@role='dialog']"):
                if d.is_displayed() and "add affiliate product" in (d.text or "").lower():
                    aff_open = True
                    break
        except Exception:
            pass

        if not aff_open:
            # Form utama kembali + Scheduling options tile visible.
            try:
                for so in driver.find_elements(By.XPATH, XPATH_SCHED_OPT):
                    if so.is_displayed():
                        return "success"
            except Exception:
                pass
        time.sleep(1)
    return "timeout"
