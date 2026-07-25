# File : includes\jobs\workflow.py
import json
import os
from flask import session
from includes.creator import get_active_creator
from includes.jobs.workflows_second_ty import WorkflowsSecondTy
from includes.jobs.workflows_toko_viral_shop import WorkflowsTokoViralShop
from includes.jobs.workflows_mirainoyume2024 import WorkflowsMiraiNoYume
from includes.jobs.workflows_KangPetruk import WorkflowsKangPetruk

from datetime import datetime

def hitung_waktu_schedule(data_json, hari_ini=None):
    """
    Fungsi untuk menghitung selisih hari serta mengambil jam dan menit dari data schedule.
    """
    # 1. Ambil string datetime dari JSON
    date_str = data_json["schedule"]["datetime"]
    
    # 2. Ubah string menjadi objek datetime
    target_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    
    # 3. Tentukan tanggal hari ini (jika tidak diinput manual, ambil dari sistem)
    if hari_ini is None:
        current_date = datetime.now().date()
    else:
        current_date = datetime.strptime(hari_ini, "%Y-%m-%d").date()
        
    # 4. Hitung selisih hari, jam, dan menit
    selisih_hari = (target_date.date() - current_date).days
    jam = target_date.hour
    menit = target_date.minute
    
    # 5. Kembalikan hasil dalam bentuk dictionary agar mudah dibaca
    return {
        "hari": selisih_hari,
        "jam": jam,
        "menit": menit
    }

def get_workflow(project_path):
    # Mengambil template workflow awal

    # Membaca file schedule.json
    schedule_path = os.path.join(project_path, "schedule.json")
    with open(schedule_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    username = data["creator"]["username"]
    if username == "second.ty" :
        jobs_json = WorkflowsSecondTy()

    # masih pake second ty json upload setting
    elif username == "mirainoyume2024" :
        jobs_json = WorkflowsMiraiNoYume()

    # masih pake second ty json upload setting
    elif username == "kang.petruk4" :
        jobs_json = WorkflowsKangPetruk()

    elif username == "toko.viral.shop" :
        jobs_json = WorkflowsTokoViralShop()

    # masih pake second ty json upload setting
    elif username == "vanice.suga" :
        jobs_json = WorkflowsSecondTy()

    else :
        jobs_json = WorkflowsSecondTy()

    keranjang_title = "Cobain mumpung promo"

    # Mengolah path video
    video_path = os.path.join(project_path, data["files"]["video"])
    
    # Mengambil data teks
    desdescription_caption = data["content"]["caption"]
    product_title = data["product"]["title"]

    # Memproses tanggal menggunakan fungsi hitung_waktu_schedule yang sebelumnya dibuat
    tanggal_upload = hitung_waktu_schedule(data)

    # Looping untuk memodifikasi jobs_json sesuai dengan ID masing-masing
    job_id = data["job_id"]
    for job in jobs_json:
        
        if job["id"] == 1:
            job["data"]["file_name"] = video_path

        elif job["id"] == 10:
            job["data"]["text"] = desdescription_caption

        elif job["id"] == 15:
            job["data"]["text"] = product_title

        elif job["id"] == 16:
            job["data"]["text"] = product_title

        elif job["id"] == 21:
            job["data"]["text"] = keranjang_title

        elif job["id"] == 26:
            job["data"]["day"] = tanggal_upload["hari"]
            job["data"]["hour"] = tanggal_upload["jam"]
            job["data"]["minute"] = tanggal_upload["menit"]

        elif job["id"] == 29:
            # Menggunakan tanda kutip tunggal di dalam f-string agar tidak bentrok dengan kutip luar
            job["data"]["remote"] = f"/sdcard/Download/{data['files']['video']}"

    # Mengembalikan data json yang sudah dimodifikasi
    return jobs_json, product_title, job_id

