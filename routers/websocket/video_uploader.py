# File : routers\websocket\video_uploader.py

import json
import os
from datetime import datetime
from includes.websocket import sock
from includes.jobs.job_runner import start_job
from includes.upload_manager import manager
from includes.jobs.facebook_job_runner import start_facebook_job
from includes.facebook_hp_manager import facebook_hp_manager
from includes.android.device_connection import device_connection


# ============================================================
# Phase 3 — Dispatch TikTok vs Facebook (server-side minimal)
# ============================================================

def _parse_register(register):
    """Parse pesan register dari Kotlin menjadi dict (bila JSON).

    Tidak memvalidasi format; bila tidak bisa di-parse, return None.
    """
    if isinstance(register, dict):
        return register

    if isinstance(register, str):
        try:
            parsed = json.loads(register)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    return None


def _resolve_platform(register):
    """
    Tentukan platform untuk SATU koneksi Android: "tiktok" / "facebook" / None.

    TANPA perubahan Kotlin / register protocol:
      1) Bila pesan register membawa "platform" ("facebook"/"tiktok"),
         dipakai langsung.
      2) Tanpa info platform, pakai heuristic queue aktif:
         - TikTok queue running  -> "tiktok"  (mempertahankan behavior existing)
         - Facebook queue running-> "facebook"
      3) Tidak ada queue aktif   -> None (koneksi idle; loop tidak jalan).

    Satu koneksi = SATU pipeline (tidak ada rebutan device antar manager).
    """
    parsed = _parse_register(register)
    if parsed is not None:
        plat = parsed.get("platform")
        if plat in ("facebook", "tiktok"):
            return plat

    if manager.running:
        return "tiktok"

    if facebook_hp_manager.running and len(facebook_hp_manager.jobs) > 0:
        return "facebook"

    return None


def _tiktok_upload_loop(ws):
    """
    Loop TikTok — DIPINDAHKAN SECARA UTUH dari handler existing.
    Logika internal TIDAK diubah (TikTok before Phase 3 == after Phase 3).
    """
    while manager.running:

        schedule_path = manager.get_next_job()

        if schedule_path is None:
            print("Tidak ada job yang menunggu.")
            break

        print("Running job:", schedule_path)

        result = start_job(
            ws=ws,
            manager=manager,
            schedule_path=schedule_path
        )

        if result:
            manager.complete_job()
        else:
            print("Job gagal, workflow dihentikan")
            break


def _facebook_upload_loop(ws):
    """
    Loop Facebook HP — TERISOLASI dari TikTok.

    - get_next_job -> FacebookHpManager (BUKAN UploadManager TikTok)
    - runner       -> start_facebook_job (BUKAN start_job TikTok)
    - completion   -> complete_job_success / complete_job_failed
    - TIDAK menyentuh upload_jobs / schedule_batches / MySQL / batch.
    - Command gagal / disconnect / exception:
        job TETAP pending (facebook_schedule.status tidak diubah),
        FacebookHpManager mencatat failure,
        lanjut ke job berikutnya (perilaku Facebook PC).
    """
    while facebook_hp_manager.running:

        schedule_path = facebook_hp_manager.get_next_job()

        if schedule_path is None:
            print("Tidak ada job Facebook yang menunggu.")
            break

        print("Running Facebook job:", schedule_path)

        try:
            result = start_facebook_job(
                ws=ws,
                manager=facebook_hp_manager,
                project_path=schedule_path,
            )
        except Exception as exc:
            # Koneksi bermasalah (mis. ws.send/receive raise saat disconnect):
            # job tetap pending, catat failure, hentikan loop.
            facebook_hp_manager.add_log(
                f"[ERROR] Exception saat menjalankan job Facebook: {exc}",
                "error",
            )
            facebook_hp_manager.complete_job_failed()
            break

        if result["success"]:
            facebook_hp_manager.complete_job_success()
        elif result.get("stopped"):
            print("Facebook job dihentikan (stop diminta).")
            break
        else:
            print("Facebook job gagal, lanjut job berikutnya")
            facebook_hp_manager.complete_job_failed()


def _handle_video_uploader_session(ws):
    """
    Body handler WebSocket — dipisahkan agar bisa di-test langsung.

    Dipanggil oleh route /service/video_uploader (fungsi `video_uploader`).
    Perilaku TIKTOK identik dengan sebelum Phase 3 (loop dipindah utuh).
    """
    start_time = datetime.now()
    print("Android Connected")

    # Phase 1: catat koneksi Android (observasi; tidak mengubah loop TikTok).
    token = device_connection.register(
        endpoint="/service/video_uploader"
    )

    try:
        register = ws.receive()
        print(register)

        # Phase 3: dispatch minimal server-side TikTok vs Facebook.
        # TIDAK mengubah Kotlin; TIDAK mengubah command protocol.
        platform = _resolve_platform(register)
        print("Platform :", platform)

        if platform == "facebook":
            _facebook_upload_loop(ws)
        else:
            _tiktok_upload_loop(ws)

    finally:
        # Phase 1: lepaskan catatan koneksi saat disconnect.
        device_connection.unregister(token)
        print(
            f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Android Disconnected"
        )

    elapsed = datetime.now() - start_time

    total = int(elapsed.total_seconds())

    jam = total // 3600
    menit = (total % 3600) // 60
    detik = total % 60

    if jam > 0:
        print(f"Waktu proses: {jam} jam, {menit} menit, {detik} detik")
    elif menit > 0:
        print(f"Waktu proses: {menit} menit, {detik} detik")
    else:
        print(f"Waktu proses: {detik} detik")


@sock.route("/service/video_uploader")
def video_uploader(ws):
    # Delegasi ke body handler (behavior route identik; flask_sock.route
    # TIDAK mengembalikan fungsi asli, hanya mendaftarkan route).
    _handle_video_uploader_session(ws)