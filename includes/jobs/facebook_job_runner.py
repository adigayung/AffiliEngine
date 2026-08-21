# File : includes\jobs\facebook_job_runner.py
"""
facebook_job_runner.py — Runner job Facebook HP (Android).

TERPISAH dari includes/jobs/job_runner.py (TikTok):
  - TIDAK memakai start_job() TikTok (lifecycle TikTok punya dependency MySQL
    upload_jobs + batch status + completion marker khusus).
  - TIDAK menyentuh upload_jobs / schedule_batches / MySQL TikTok.
  - TIDAK memakai set_schedule_time (Facebook mengisi tanggal/waktu lewat
    input_text) dan TIDAK memakai pull_file / delete_file.

Reuse existing:
  - AndroidDevice (includes/android/device.py) — command executor.
  - Command protocol existing (click, input_text, clear_text, push_file,
    read_text, screenshot) — TIDAK membuat command baru.
  - includes/facebook_uploader (load_schedule, validate_schedule_data,
    build_job_data) — data schedule.
  - includes/jobs/workflows_facebook — template workflow Facebook HP,
    SEJAJAR dengan workflows_KangPetruk.py / workflows_second_ty.py (TikTok).
    build_facebook_workflow() di bawah memakai WorkflowsFacebook() lalu
    inject nilai dinamis by id — mekanisme SAMA dengan get_workflow TikTok
    (includes/jobs/workflow.py).
  - includes/facebook_persistence — mark facebook_schedule.status = success
    (temp file -> os.replace -> verify), pola terbukti Facebook PC.

Perilaku failure:
  - command/workflow gagal -> failed (status tetap pending), default lanjut
    ke job berikutnya seperti Facebook PC (keputusan lanjut ada di konsumen).
  - persistence gagal      -> JANGAN dianggap sukses (status tetap pending).
"""

import os
from datetime import datetime

from includes.android.device import AndroidDevice
from includes.facebook_persistence import mark_facebook_success
from includes.facebook_uploader import (
    FacebookUploaderError,
    build_job_data,
    load_schedule,
    validate_schedule_data,
)
from includes.jobs.workflows_facebook import WorkflowsFacebook

# ============================================================
# Konstanta dinamis — pola TikTok (remote path + format schedule)
# ============================================================
FB_REMOTE_DIR = "/sdcard/Download"

# Teks Link name affiliate — SAMA dengan Facebook PC (affiliate.py).
FB_LINK_NAME_TEXT = "Cobain Mumpung PROMO!"

SCHEDULE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def build_facebook_workflow(job_data, remote_dir=FB_REMOTE_DIR):
    """
    Bangun workflow Facebook HP dari job_data — POLA get_workflow TikTok.

    WorkflowsFacebook() mengembalikan deepcopy template (jobs_json),
    lalu nilai dinamis di-inject melalui id (mekanisme sama persis dengan
    includes/jobs/workflow.py::get_workflow yang mutasi by id).

    id yang di-inject:
        1  -> file_name (video path local) & remote (path Android)
        7  -> caption
        11 -> affiliate URL
        13 -> Link name
        17 -> tanggal jadwal (dd MMM yyyy)
        19 -> waktu jadwal  (HH:mm)

    Args:
        job_data: dict dari build_job_data(data, job_dir) — berisi
                  video_name, video_path, caption, affiliate_link,
                  facebook_schedule (datetime string), dll.
        remote_dir: folder remote sementara untuk video di Android.

    Returns:
        list[dict] — job command format TikTok: {id, cmd, delay, status,
                     keterangan, data}. Koordinat klik tetap placeholder
                     (0, 0) — diisi manual oleh pengguna.
    """
    video_name = job_data["video_name"]
    video_path = job_data["video_path"]
    caption = job_data["caption"]
    affiliate_link = job_data["affiliate_link"]
    sched_str = job_data["facebook_schedule"]

    # Parsing jadwal — format sama dengan Facebook PC scheduling.py.
    sched_dt = datetime.strptime(sched_str, SCHEDULE_DATETIME_FORMAT)
    date_display = sched_dt.strftime("%d %b %Y")
    time_display = sched_dt.strftime("%H:%M")

    # Remote path Android SELALU pakai forward slash (bukan os.path.join,
    # yang di Windows menghasilkan backslash salah di Android).
    remote_video = remote_dir.rstrip("/\\") + "/" + video_name

    workflow = WorkflowsFacebook()

    for job in workflow:
        if job["id"] == 1:
            job["data"]["file_name"] = video_path
            job["data"]["remote"] = remote_video
        elif job["id"] == 7:
            job["data"]["text"] = caption
        elif job["id"] == 11:
            job["data"]["text"] = affiliate_link
        elif job["id"] == 13:
            job["data"]["text"] = FB_LINK_NAME_TEXT
        elif job["id"] == 17:
            job["data"]["text"] = date_display
        elif job["id"] == 19:
            job["data"]["text"] = time_display

    return workflow


def start_facebook_job(ws, manager, project_path):
    """
    Jalankan SATU project Facebook HP dari awal sampai selesai.

    Args:
        ws: koneksi WebSocket ke aplikasi Android (command protocol existing).
        manager: FacebookHpManager (untuk log).
        project_path: folder project (berisi schedule.json + video).

    Returns:
        dict:
            {"success": bool, "stopped": bool, "stage": str, "error": str|None}
            success=True  -> seluruh command sukses DAN persistence success.
            success=False -> command gagal / load gagal / persistence gagal.
            stopped=True  -> stop diminta di tengah workflow.
    """
    device = AndroidDevice(ws)

    manager.add_log(f"[INFO] Facebook HP job dimulai: {project_path}", "info")

    # ============================================================
    # Load + validasi (reuse helper Facebook existing)
    # ============================================================
    try:
        schedule_path = os.path.join(project_path, "schedule.json")
        data = load_schedule(schedule_path)
        fb_status = validate_schedule_data(data)

        if fb_status != "pending":
            manager.add_log(
                "[INFO] facebook_schedule.status bukan 'pending' — job dilewati.",
                "skip",
            )
            return {
                "success": False,
                "stopped": False,
                "stage": "validate",
                "error": f"facebook_schedule.status = {fb_status!r}",
            }

        job_data = build_job_data(data, project_path)
        workflow = build_facebook_workflow(job_data)

    except FacebookUploaderError as exc:
        manager.add_log(f"[ERROR] Gagal load/validasi schedule: {exc}", "error")
        return {
            "success": False,
            "stopped": False,
            "stage": "load",
            "error": str(exc),
        }
    except Exception as exc:
        manager.add_log(f"[ERROR] Gagal memproses job: {exc}", "error")
        return {
            "success": False,
            "stopped": False,
            "stage": "load",
            "error": str(exc),
        }

    manager.add_log(f"[INFO] Job data video : {job_data['video_name']}", "info")
    manager.add_log(f"[INFO] Facebook schedule: {job_data['facebook_schedule']}", "info")

    # ============================================================
    # Jalankan command satu per satu
    # ============================================================
    for job in workflow:
        if manager.stop_requested:
            manager.add_log("Stop diminta — workflow dihentikan.", "warning")
            return {
                "success": False,
                "stopped": True,
                "stage": job["keterangan"],
                "error": "stop_requested",
            }

        if job["status"] != "pending":
            continue

        manager.add_log(f"Running job: {job['id']} — {job['cmd']}")
        manager.add_log(f"Keterangan : {job['keterangan']}", "info")

        result = execute_facebook_command(device, job, manager)

        if result:
            job["status"] = "done"
            manager.add_log(f"Job Done: {job['id']}", "success")
        else:
            job["status"] = "failed"
            manager.add_log(f"Job Failed: {job['id']} — {job['cmd']}", "error")
            manager.add_log(
                f"[ERROR] Gagal pada tahap: {job['keterangan']}", "error"
            )
            manager.add_log(
                "[INFO] facebook_schedule.status tetap pending.", "info"
            )
            return {
                "success": False,
                "stopped": False,
                "stage": job["keterangan"],
                "error": f"command failed: {job['cmd']} (id={job['id']})",
            }

    # ============================================================
    # Semua command sukses -> persistence success
    # ============================================================
    manager.add_log(
        "[INFO] Seluruh command berhasil. Menyimpan facebook_schedule.status -> success",
        "info",
    )
    marked = mark_facebook_success(project_path, log_fn=manager.add_log)

    if marked:
        manager.add_log("[SUCCESS] Facebook HP job selesai & status success tersimpan.", "success")
        return {
            "success": True,
            "stopped": False,
            "stage": "completed",
            "error": None,
        }

    # Persistence gagal — JANGAN anggap job sukses.
    manager.add_log(
        "[ERROR] Gagal menyimpan status success — job TIDAK dianggap sukses (status tetap pending).",
        "error",
    )
    return {
        "success": False,
        "stopped": False,
        "stage": "persist",
        "error": "persistence failed (status tetap pending)",
    }


def execute_facebook_command(device, job, manager):
    """
    Eksekusi SATU command. Hanya command existing (tanpa set_schedule_time,
    tanpa pull_file/delete_file, tanpa compare_title/MySQL).

    Returns:
        bool: True sukses, False gagal / tidak dikenal.
    """
    cmd = job["cmd"]
    data = job["data"]
    delay = job.get("delay", 0)

    if cmd == "click":
        return device.click(target=data["target"], delay=delay)

    elif cmd == "input_text":
        return device.input_text(
            target=data["target"],
            text=data["text"],
            delay=delay,
        )

    elif cmd == "clear_text":
        return device.clear_text(target=data["target"], delay=delay)

    elif cmd == "push_file":
        result = device.push_file(
            local_path=data["file_name"],
            remote_path=data["remote"],
            mime=data.get("mime", "video/mp4"),
        )
        # push_file mengembalikan dict response (bukan bool). Response dengan
        # success=False TETAP dict (truthy) -> harus dicek eksplisit.
        if isinstance(result, dict):
            return result.get("success", False)
        return bool(result)

    elif cmd == "read_text":
        text = device.read_text(
            target=data["target"],
            delay=delay,
        )
        if text is None:
            manager.add_log("Read Text : FAILED", "error")
            return False

        manager.add_log(f"Read Text : {text}")
        expected = data.get("expected", "")
        manager.add_log(f"Expected  : {expected}")

        if expected in (text or ""):
            manager.add_log("Verifikasi teks cocok", "success")
            return True

        manager.add_log("Verifikasi teks TIDAK cocok", "error")
        return False

    elif cmd == "screenshot":
        return bool(device.screenshot())

    else:
        manager.add_log(f"Unknown command: {cmd}", "error")
        return False
