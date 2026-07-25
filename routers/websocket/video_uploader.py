# File : routers\websocket\video_uploader.py

import json
import os
from datetime import datetime
from includes.websocket import sock
from includes.jobs.job_runner import start_job
from includes.upload_manager import manager

@sock.route("/service/video_uploader")
def video_uploader(ws):
    start_time = datetime.now()
    print("Android Connected")

    try:
        register = ws.receive()
        print(register)

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

    finally:
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