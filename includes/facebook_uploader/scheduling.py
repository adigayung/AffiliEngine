"""
scheduling.py — Alur scheduling: Scheduling options, isi Date, isi Time,
Schedule for later, verifikasi dialog tertutup, final Schedule.

Selector, format Date/Time, dan urutan IDENTIK dengan main.py golden version.
"""

import datetime
import time

from .exceptions import SchedulingError
from .pacing import DELAY_MAJOR, DELAY_MICRO, DELAY_NORMAL, human_delay
from .selectors import XPATH_FINAL_SCHEDULE, XPATH_SCHED_LATER, XPATH_SCHED_OPT
from .waits import (
    _click_element,
    _clickable_ancestor,
    _selenium_keys,
    _wait_sched_date_input,
    _wait_sched_dialog_closed,
    _wait_sched_dialog_visible,
    _wait_sched_time_input,
    _wait_schedule_finish,
    _wait_visible,
)


def run_scheduling(driver, sched_str):
    """
    Jalankan seluruh alur scheduling.

    sched_str: nilai facebook_schedule.datetime dari schedule.json
    (format 'YYYY-MM-DD HH:MM:SS'). Bukan waktu komputer.
    """
    print("[INFO] Starting Stage 5 - Scheduling")

    # 1. Klik "Scheduling options" (tile, role=button, ber-TEKS)
    try:
        so_el = _wait_visible(driver, XPATH_SCHED_OPT, 30, "Scheduling options tile")
    except Exception:
        print("[ERROR] Scheduling options not found")
        raise SchedulingError("Scheduling options not found")
    human_delay(DELAY_NORMAL, "before Scheduling options")
    print("[INFO] Clicking Scheduling options")
    try:
        _click_element(driver, _clickable_ancestor(driver, so_el))
    except Exception:
        print("[ERROR] Failed to click Scheduling options")
        raise SchedulingError("Failed to click Scheduling options")
    try:
        _wait_sched_dialog_visible(driver, timeout=30)
    except Exception:
        print("[ERROR] Scheduling options dialog did not appear")
        raise SchedulingError("Scheduling options dialog did not appear")
    print("[INFO] Scheduling options dialog detected")

    # 2. Ambil jadwal DARI schedule.json (bukan waktu komputer).
    try:
        sched_dt = datetime.datetime.strptime(sched_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        print("[ERROR] Cannot parse facebook_schedule.datetime:", repr(sched_str))
        raise SchedulingError(f"Cannot parse facebook_schedule.datetime: {sched_str!r}")
    date_display = sched_dt.strftime("%d %b %Y")
    time_display = sched_dt.strftime("%H:%M")
    print("[INFO] Schedule date from schedule.json:", sched_dt.strftime("%Y-%m-%d"))
    print("[INFO] Schedule time from schedule.json:", sched_dt.strftime("%H:%M"))

    # 3. Date field (kontekstual di dialog Scheduling options).
    try:
        date_el = _wait_sched_date_input(driver, timeout=30)
    except Exception:
        print("[ERROR] Date input not found")
        raise SchedulingError("Date input not found")
    human_delay(DELAY_NORMAL, "before Date fill")
    print("[INFO] Current Date value:", date_el.get_attribute("value"))
    _fill_sched_input(driver, date_el, date_display)
    time.sleep(1)
    actual_date = date_el.get_attribute("value")
    if actual_date != date_display:
        print("[ERROR] Date field mismatch:")
        print("Expected:", date_display)
        print("Actual:  ", actual_date)
        raise SchedulingError("Date field mismatch")
    print("[INFO] Date field verified:", actual_date)

    human_delay(DELAY_MICRO)

    # 4. Time field.
    try:
        time_el = _wait_sched_time_input(driver, timeout=30)
    except Exception:
        print("[ERROR] Time input not found")
        raise SchedulingError("Time input not found")
    print("[INFO] Current Time value:", time_el.get_attribute("value"))
    _fill_sched_input(driver, time_el, time_display)
    time.sleep(1)
    actual_time = time_el.get_attribute("value")
    if actual_time != time_display:
        print("[ERROR] Time field mismatch:")
        print("Expected:", time_display)
        print("Actual:  ", actual_time)
        raise SchedulingError("Time field mismatch")
    print("[INFO] Time field verified:", actual_time)

    # 5. "Schedule for later" (pilih yang visible; ada versi tersembunyi di form utama).
    try:
        later_el = _wait_visible(driver, XPATH_SCHED_LATER, 30, "Schedule for later button")
    except Exception:
        print("[ERROR] Schedule for later button not found")
        raise SchedulingError("Schedule for later button not found")
    human_delay(DELAY_NORMAL, "before Schedule for later")
    print("[INFO] Clicking Schedule for later")
    try:
        _click_element(driver, _clickable_ancestor(driver, later_el))
    except Exception:
        print("[ERROR] Failed to click Schedule for later")
        raise SchedulingError("Failed to click Schedule for later")
    human_delay(DELAY_MAJOR, "after Schedule for later")
    try:
        _wait_sched_dialog_closed(driver, timeout=30)
    except Exception:
        print("[ERROR] Scheduling dialog did not close")
        raise SchedulingError("Scheduling dialog did not close")
    print("[INFO] Scheduling dialog closed")

    # 6. Final "Schedule" (aria-label='Schedule', role='button', visible).
    try:
        final_el = _wait_visible(driver, XPATH_FINAL_SCHEDULE, 30, "Final Schedule button")
    except Exception:
        print("[ERROR] Final Schedule button not found")
        raise SchedulingError("Final Schedule button not found")
    print("[INFO] Final Schedule button found")
    human_delay(DELAY_NORMAL, "before final Schedule")
    print("[INFO] Clicking final Schedule")
    try:
        _click_element(driver, _clickable_ancestor(driver, final_el))
    except Exception:
        print("[ERROR] Failed to click final Schedule")
        raise SchedulingError("Failed to click final Schedule")

    # 7. Tunggu indikasi request scheduling selesai.
    print("[INFO] Waiting for scheduling request to complete...")
    if not _wait_schedule_finish(driver, timeout=60):
        print("[ERROR] Final Schedule state could not be verified")
        raise SchedulingError("Final Schedule state could not be verified")
    print("[INFO] Stage 5 completed successfully")
    print("[INFO] Scheduling finished")
    print("[INFO] Stopping after final Schedule")


def _fill_sched_input(driver, el, value):
    """
    Isi field Date/Time. Jika nilai sudah sesuai target, tidak diketik ulang.
    Gunakan select-all + delete (clear() React sering gagal lalu teks menumpuk).
    """
    Keys = _selenium_keys()
    try:
        if (el.get_attribute("value") or "").strip() == value:
            return value
    except Exception:
        pass
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].focus();", el)
    try:
        el.send_keys(Keys.CONTROL, "a")
        el.send_keys(Keys.DELETE)
    except Exception:
        pass
    el.send_keys(value)
    time.sleep(0.5)
    return el.get_attribute("value")
