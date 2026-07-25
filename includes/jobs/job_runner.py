# File : includes\jobs\job_runner.py
import time
import json
import os

from includes.jobs.workflow import get_workflow
from includes.android.device import AndroidDevice
from includes.verification_product import compare_title
from includes.utils import save_workflow
from includes.mysql import update_upload_job, check_and_update_batch_status

def start_job(ws, manager, schedule_path):

    device = AndroidDevice(ws)

    jobs_json, product_title, job_id = get_workflow(schedule_path)
    print (manager.running)
    print("schedule_path :", schedule_path)
    if not manager.running:
        manager.add_log("Upload Manager tidak aktif, job dibatalkan", "warning")
        return False
    
    print("===================================")
    print("schedule_path :", schedule_path)
    print("jumlah job :", len(jobs_json))

    for job in jobs_json:
        print(job["id"], job["status"], job["cmd"])
        if manager.stop_requested:

            manager.add_log(
                "Stop diminta oleh user",
                "warning"
            )

            manager.stop()

            return False
        
        if job["status"] != "pending":
            continue

        manager.add_log(f"Running job: {job['id']}")
        manager.add_log(f"Perintah : {job['cmd']}")
        manager.add_log(f"Keterangan : {job['keterangan']}", "success")

        result = execute_job(
            device,
            job,
            manager,
            product_title
        )

        if result:

            job["status"] = "done"

            manager.add_log(f"Job Done: {job['id']}", "success")

        else:

            job["status"] = "failed"

            manager.add_log(f"Job Failed: {job['id']}", "error")
            manager.add_log("Workflow dihentikan karena job gagal", "danger")
            manager.stop()
            # Hentikan seluruh workflow jika ada job yang gagal
            return False
        
        if result and job["keterangan"] == "Klik Draft ( KELAR ! )'":
            update_upload_job(job_id, "uploaded")

            # Ambil batch_id dari schedule.json untuk pengecekan batch
            schedule_json_path = os.path.join(schedule_path, "schedule.json")
            if os.path.exists(schedule_json_path):
                with open(schedule_json_path, 'r', encoding='utf-8') as f:
                    schedule_data = json.load(f)
                batch_id = schedule_data.get("batch_id")
                if batch_id:
                    check_and_update_batch_status(batch_id)
            
    print("===================================")
    save_workflow(
        schedule_path,
        "success"
    )

    # Semua job berhasil
    return True

def execute_job(device, job, manager, product_title):

    cmd = job["cmd"]

    if cmd == "click":

        return device.click(
            target=job["data"]["target"],
            delay=job["delay"]
        )

    elif cmd == "push_file":

        return device.push_file(
            local_path=job["data"]["file_name"],
            remote_path=job["data"]["remote"],
            mime=job["data"].get("mime", "application/octet-stream")
        )

    elif cmd == "pull_file":

        return device.pull_file(
            remote_path=job["data"]["remote"],
            local_path=job["data"]["file_name"]
        )

    elif cmd == "delete_file":

        return device.delete_file(
            remote_path=job["data"]["remote"]
        )

    elif cmd == "input_text":
        hh = device.input_text(
            target=job["data"]["target"],
            text=job["data"]["text"],
            delay=job["delay"]
        )
        manager.add_log(f"Masuk input_text")
        return hh
        

    elif cmd == "screenshot":

        return device.screenshot()

    elif cmd == "read_text":

        text = device.read_text(
            target=job["data"]["target"],
            delay=job.get("delay", 0)
        )

        if text is None:

            manager.add_log("Read Text : FAILED", "error")

            return False

        manager.add_log(f"Read Text : {text}")

        expected = product_title

        manager.add_log(f"Expected : {expected}")

        result = compare_title(expected, text)

        manager.add_log(f"Compare : {result}")

        if result:

            manager.add_log("Product sama", "success")

            return True

        manager.add_log("Product TIDAK sama", "error")

        return False

    elif cmd == "set_schedule_time":

        return device.set_schedule_time(
            day=job["data"]["day"],
            hour=job["data"]["hour"],
            minute=job["data"]["minute"],
            delay=job["delay"]
        )

    else:

        manager.add_log(f"Unknown command: {cmd}", "error")
        manager.stop()
        return False
