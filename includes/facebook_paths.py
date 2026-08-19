# File : includes\facebook_paths.py
"""
facebook_paths.py — Validasi project path untuk Facebook Uploader.

Membaca upload_schedule.json (sumber daftar project SAMA seperti TikTok
uploader), lalu memvalidasi setiap project path secara individual terhadap
aturan Facebook.

Aturan validasi (READ-ONLY terhadap schedule.json, tidak pernah menulis):
    1. Project path harus ada.
    2. schedule.json harus ada & valid JSON.
    3. files.video harus ada.
    4. Ukuran file video minimal 1 MB.
    5. product.shopee_affiliate_link harus tersedia & tidak kosong.
    6. facebook_schedule harus tersedia.
    7. facebook_schedule.datetime harus tersedia & valid.
    8. facebook_schedule.status:
         - "pending"  -> VALID (masuk textbox)
         - "success"  -> COMPLETED (sudah selesai, jangan di-upload ulang)
         - lainnya    -> INVALID / skip
"""

import json
import os
from datetime import datetime

MIN_VIDEO_SIZE = 1024 * 1024  # 1 MB

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_facebook_datetime(value):
    """Parse facebook_schedule.datetime. Return datetime atau None bila invalid."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, DATETIME_FORMAT)
    except ValueError:
        return None


def validate_facebook_path(path):
    """Validasi satu project path untuk Facebook upload. READ-ONLY.

    Args:
        path: Path absolut ke folder project video.

    Returns:
        dict dengan keys:
            status          : 'valid' | 'completed' | 'invalid'
            reason          : str — alasan status
            video_name      : str | None
            video_size_mb   : float | None
            schedule_data   : dict | None — isi schedule.json (untuk job_data)
            facebook_datetime : str | None
            affiliate_link  : str | None
    """
    path = str(path or "").strip()

    base = {
        "status": "invalid",
        "reason": "",
        "video_name": None,
        "video_size_mb": None,
        "schedule_data": None,
        "facebook_datetime": None,
        "affiliate_link": None,
    }

    # 1. Project path harus ada
    if not path:
        base["reason"] = "Project path kosong"
        return base
    if not os.path.isdir(path):
        base["reason"] = f"Project path tidak ditemukan: {path}"
        return base

    # 2. schedule.json harus ada & valid
    schedule_path = os.path.join(path, "schedule.json")
    if not os.path.isfile(schedule_path):
        base["reason"] = "schedule.json tidak ditemukan"
        return base
    try:
        with open(schedule_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        base["reason"] = "schedule.json tidak dapat dibaca / format tidak valid"
        return base
    if not isinstance(data, dict):
        base["reason"] = "schedule.json tidak valid (bukan objek JSON)"
        return base
    base["schedule_data"] = data

    # 3. files.video harus ada
    video_name = (data.get("files") or {}).get("video") or ""
    if not video_name:
        base["reason"] = "files.video tidak tersedia"
        return base
    video_path = os.path.join(path, video_name)
    if not os.path.isfile(video_path):
        base["reason"] = f"Video tidak ditemukan: {video_name}"
        return base
    base["video_name"] = video_name

    # 4. Ukuran video minimal 1 MB
    size_bytes = os.path.getsize(video_path)
    size_mb = size_bytes / (1024 * 1024)
    base["video_size_mb"] = size_mb
    if size_bytes < MIN_VIDEO_SIZE:
        base["reason"] = f"Video size {size_mb:.2f} MB (< 1 MB)"
        return base

    # 5. product.shopee_affiliate_link wajib tersedia
    affiliate = (data.get("product") or {}).get("shopee_affiliate_link") or ""
    affiliate = str(affiliate).strip()
    if not affiliate:
        base["reason"] = "Shopee affiliate link tidak tersedia"
        return base
    base["affiliate_link"] = affiliate

    # 6. facebook_schedule harus tersedia
    fb = data.get("facebook_schedule")
    if not isinstance(fb, dict):
        base["reason"] = "facebook_schedule tidak tersedia"
        return base

    # 7. facebook_schedule.datetime harus valid
    fb_dt = fb.get("datetime") or ""
    if not parse_facebook_datetime(fb_dt):
        base["reason"] = f"facebook_schedule.datetime tidak valid: {fb_dt!r}"
        return base
    base["facebook_datetime"] = str(fb_dt).strip()

    # 8. facebook_schedule.status
    status = str(fb.get("status") or "").strip().lower()
    if status == "success":
        base["status"] = "completed"
        base["reason"] = "facebook_schedule.status = success"
        return base
    if status != "pending":
        base["reason"] = f"facebook_schedule.status tidak valid: {fb.get('status')!r}"
        return base

    base["status"] = "valid"
    base["reason"] = "Siap upload"
    return base


def validate_facebook_batch(file):
    """Validasi seluruh project dari upload_schedule.json yang di-upload user.

    Args:
        file: FileStorage dari request.files (workflow JSON upload_schedule.json).

    Returns:
        dict:
            paths   : list[str] — hanya path VALID (pending & lolos semua aturan).
            summary : {total, valid, completed, invalid}
            details : list[(level, text)] — log detail per project untuk UI.

    Raises:
        ValueError bila format JSON / field 'folders' tidak valid.
    """
    workflow = json.load(file)
    folders = workflow.get("folders")
    if not isinstance(folders, list):
        raise ValueError("Field 'folders' tidak valid.")

    paths = []
    summary = {"total": 0, "valid": 0, "completed": 0, "invalid": 0}
    details = []

    for folder in folders:
        if not isinstance(folder, dict):
            continue
        path = str(folder.get("path") or "").strip()
        if not path:
            continue
        summary["total"] += 1

        result = validate_facebook_path(path)

        if result["status"] == "valid":
            summary["valid"] += 1
            paths.append(path)
            details.append(("valid", f"[VALID] {result['video_name']}"))
            details.append(("info", f"    Facebook schedule: {result['facebook_datetime']}"))
            details.append(("info", f"    Shopee affiliate link: tersedia"))
        elif result["status"] == "completed":
            summary["completed"] += 1
            name = result["video_name"] or os.path.basename(path.rstrip("\\/")) or path
            details.append(("completed", f"[COMPLETED] {name} — {result['reason']}"))
        else:
            summary["invalid"] += 1
            name = result["video_name"] or os.path.basename(path.rstrip("\\/")) or path
            details.append(("skip", f"[SKIP] {name} — {result['reason']}"))

    return {
        "paths": paths,
        "summary": summary,
        "details": details,
    }
