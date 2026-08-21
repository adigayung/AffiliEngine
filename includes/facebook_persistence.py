"""
facebook_persistence.py — Persistence facebook_schedule.status = "success".

Helper STANDALONE yang meniru persis mekanisme yang sudah terbukti di
includes/facebook_upload_manager.py (Facebook PC):

    temp file -> os.replace (atomic) -> verify ulang hasil write

Read -> Modify -> Write secara aman. HANYA mengubah
data["facebook_schedule"]["status"]; field lain dan format file
(indent=4, ensure_ascii=False) dipertahankan — sama seperti
write_json di includes/schedule/folder.py.

Dibuat sebagai modul terpisah agar Facebook HP (Phase 2) dan Facebook PC
dapat memakai mekanisme yang sama tanpa mengubah behavior PC yang sudah
terbukti. File includes/facebook_upload_manager.py TIDAK disentuh.
"""

import json
import os


def mark_facebook_success(project_path, log_fn=None):
    """
    Tandai facebook_schedule.status = "success" pada schedule.json project.

    Args:
        project_path: path absolut ke folder project (berisi schedule.json).
        log_fn: optional callable(text, level="info") untuk logging.
                Default None -> tidak ada log.

    Returns:
        True  -> status berhasil ditulis & diverifikasi.
        False -> gagal (file hilang / JSON corrupt / struktur invalid /
                  gagal tulis / verifikasi gagal).
    """
    if log_fn is None:
        def log_fn(text, level="info"):
            print(text)

    schedule_path = os.path.join(project_path, "schedule.json")

    # --- Read ---
    try:
        with open(schedule_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        log_fn(f"[ERROR] schedule.json tidak ditemukan: {schedule_path}", "error")
        return False
    except json.JSONDecodeError as exc:
        log_fn(
            f"[ERROR] schedule.json corrupt: {schedule_path}\n  Detail: {exc}",
            "error",
        )
        return False
    except OSError as exc:
        log_fn(
            f"[ERROR] Tidak dapat membaca schedule.json: {schedule_path}\n  Detail: {exc}",
            "error",
        )
        return False

    # --- Pastikan facebook_schedule ada ---
    fb = data.get("facebook_schedule")
    if not isinstance(fb, dict):
        log_fn(
            f"[ERROR] facebook_schedule tidak ditemukan / invalid: {schedule_path}",
            "error",
        )
        return False

    # --- Modify: HANYA status ---
    fb["status"] = "success"

    # --- Write aman (temp + replace, atomic) ---
    tmp_path = schedule_path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(tmp_path, schedule_path)
    except OSError as exc:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        log_fn(
            f"[ERROR] Gagal menulis schedule.json: {schedule_path}\n  Detail: {exc}",
            "error",
        )
        return False

    # --- Verifikasi hasil write ---
    try:
        with open(schedule_path, "r", encoding="utf-8") as f:
            check = json.load(f)
        if check.get("facebook_schedule", {}).get("status") != "success":
            log_fn(
                f"[ERROR] Verifikasi gagal — status bukan 'success': {schedule_path}",
                "error",
            )
            return False
    except Exception as exc:
        log_fn(
            f"[ERROR] Verifikasi hasil write gagal: {schedule_path}\n  Detail: {exc}",
            "error",
        )
        return False

    log_fn(f"[INFO] Facebook schedule marked success: {schedule_path}", "info")
    return True
