# File : includes\upload_manager.py

from datetime import datetime
import json
import os
from bs4 import BeautifulSoup
from includes.mysql import get_tiktok_id_product


class UploadManager:

    def __init__(self):

        self.running = False
        self.progress = 0
        self.logs = []
        self.jobs = []
        self.stop_requested = False

        # Upload Information Panel tracking
        self.current_job_path = None
        self.total_jobs_count = 0
        self.success_count = 0
        self.current_job_start_time = None
        self.current_schedule_data = None
        self.batch_folder = None

        print("UploadManager Created")

    # =====================================================
    # video_uploader mengambil 1 job
    # =====================================================

    def get_next_job(self):

        if not self.running:
            return None

        if len(self.jobs) == 0:
            return None

        self.current_job_path = self.jobs[0]
        self.current_job_start_time = datetime.now()

        # Baca schedule.json untuk current job
        schedule_path = os.path.join(self.current_job_path, "schedule.json")
        if os.path.exists(schedule_path):
            try:
                with open(schedule_path, "r", encoding="utf-8") as f:
                    self.current_schedule_data = json.load(f)
            except Exception:
                self.current_schedule_data = None
        else:
            self.current_schedule_data = None

        return self.current_job_path

    # =====================================================
    # Job selesai -> lanjut job berikutnya
    # =====================================================

    def complete_job(self):

        if self.jobs:
            self.jobs.pop(0)
            self.success_count += 1

        self.progress = 0
        self.current_job_path = None
        self.current_schedule_data = None
        self.current_job_start_time = None

        if len(self.jobs) == 0:
            self.finish()

    # =====================================================
    # Mulai Upload (Dipanggil dari Flask)
    # =====================================================

    def start(self, data):

        if self.running:
            return {
                "success": False,
                "message": "Upload masih berjalan."
            }

        self.jobs.clear()
        self.stop_requested = False
        directory_set = set()

        path_list = data.get("path_list", "")

        for path in path_list.splitlines():

            path = path.strip()

            if not path:
                continue

            if path in directory_set:
                continue

            if not os.path.isdir(path):
                print(f"Folder tidak ditemukan : {path}")
                continue

            schedule_path = os.path.join(path, "schedule.json")

            if not os.path.exists(schedule_path):

                print(f"schedule.json tidak ditemukan : {path}")

                continue

            try:

                with open(schedule_path, "r", encoding="utf-8") as file:

                    schedule = json.load(file)

            except Exception as e:

                print(e)

                continue

            status = schedule.get("schedule", {}).get("status", "").lower()

            if status != "pending":
                continue

            directory_set.add(path)

            self.jobs.append(path)

        if len(self.jobs) == 0:

            return {
                "success": False,
                "message": "Tidak ada folder yang dapat diproses."
            }

        self.running = True
        self.progress = 0
        self.logs.clear()

        self.total_jobs_count = len(self.jobs)
        self.success_count = 0
        self.current_job_path = None
        self.current_schedule_data = None
        self.current_job_start_time = None

        # Cari batch folder dari parent folder pertama
        if self.jobs:
            parent_dir = os.path.dirname(self.jobs[0])
            upload_schedule_path = os.path.join(parent_dir, "upload_schedule.json")
            if os.path.exists(upload_schedule_path):
                self.batch_folder = parent_dir
            else:
                self.batch_folder = None
        else:
            self.batch_folder = None

        self.add_log(
            f"Queue berhasil dibuat. <b>{len(self.jobs)}</b> job siap diproses.",
            "success"
        )

        return {
            "success": True,
            "total_job": len(self.jobs)
        }

    # =====================================================
    # Stop Upload
    # =====================================================

    def stop(self):

        if not self.running:

            return {
                "success": False,
                "message": "Tidak ada upload yang berjalan."
            }

        self.running = False
        self.stop_requested = False
        self.current_job_path = None
        self.current_schedule_data = None
        self.current_job_start_time = None

        self.add_log(
            "Stop diminta oleh pengguna.",
            "warning"
        )

        return {
            "success": True
        }

    def request_stop(self):

        self.stop_requested = True
    # =====================================================
    # Semua Upload Selesai
    # =====================================================

    def finish(self):

        self.running = False

        self.progress = 100
        self.current_job_path = None
        self.current_schedule_data = None
        self.current_job_start_time = None

        self.add_log(
            "🎉 Semua upload telah selesai.",
            "success"
        )

    # =====================================================
    # Error
    # =====================================================

    def error(self, message):

        self.running = False
        self.current_job_path = None
        self.current_schedule_data = None
        self.current_job_start_time = None

        self.add_log(
            message,
            "danger"
        )

    # =====================================================
    # Progress
    # =====================================================

    def set_progress(self, value):

        self.progress = value

    # =====================================================
    # HTML Log
    # =====================================================

    def add_log(self, text, level="info"):

        now = datetime.now().strftime("%H:%M:%S")

        colors = {

            "info": "#4dabf7",

            "success": "#51cf66",

            "warning": "#fcc419",

            "danger": "#ff6b6b"

        }

        icons = {

            "info": "\U0001f5c8\ufe0f",

            "success": "\u2705",

            "warning": "\u26a0\ufe0f",

            "danger": "\u274c"

        }

        color = colors.get(level, "#ffffff")

        icon = icons.get(level, "\u2022")

        html = f"""
        <div style="line-height:1.25">
            <span style="color:#666">[{now}]</span>
            <span style="color:{color}">{icon}</span>
            <span>{text}</span>
        </div>
        """

        self.logs.append(html)

        if len(self.logs) > 300:
            self.logs = self.logs[-300:]
        text_clean = BeautifulSoup(text, "html.parser").get_text()
        print(f"[{now}] {text_clean}")

    # =====================================================
    # Status Browser
    # =====================================================

    def status(self):

        # ============================================================
        # Hitung nilai-nilai dasar yang dibutuhkan
        # ============================================================
        total_jobs = self.total_jobs_count
        success_count = self.success_count
        remaining = len(self.jobs)
        progress_persen = round((success_count / total_jobs) * 100) if total_jobs > 0 else 0

        # ============================================================
        # Upload Range (dari upload_schedule.json)
        # ============================================================
        upload_range_text = ""
        if self.batch_folder:
            upload_schedule_path = os.path.join(self.batch_folder, "upload_schedule.json")
            if os.path.exists(upload_schedule_path):
                try:
                    with open(upload_schedule_path, "r", encoding="utf-8") as f:
                        batch_data = json.load(f)
                    sched = batch_data.get("schedule", {})
                    start_str = sched.get("start_datetime")
                    finish_str = sched.get("finish_datetime")
                    if start_str and finish_str:
                        start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                        finish_dt = datetime.strptime(finish_str, "%Y-%m-%d %H:%M:%S")
                        diff = finish_dt - start_dt
                        days = diff.days
                        hours = diff.seconds // 3600
                        if days > 0 or hours > 0:
                            parts = []
                            if days > 0:
                                parts.append(f"{days} Hari")
                            if hours > 0:
                                parts.append(f"{hours} Jam")
                            upload_range_text = " ".join(parts)
                except Exception:
                    pass

        # ============================================================
        # Data untuk card Creator Information
        # ============================================================
        creator_info = None
        if self.current_schedule_data:
            creator = self.current_schedule_data.get("creator", {})
            username = creator.get("username", "")
            creator_info = {
                "username": username,
                "avatar": f"/static/avatar/{username}.jpeg" if username else "",
            }
        elif self.batch_folder:
            upload_schedule_path = os.path.join(self.batch_folder, "upload_schedule.json")
            if os.path.exists(upload_schedule_path):
                try:
                    with open(upload_schedule_path, "r", encoding="utf-8") as f:
                        batch_data = json.load(f)
                    creator = batch_data.get("creator", {})
                    username = creator.get("username", "")
                    creator_info = {
                        "username": username,
                        "avatar": f"/static/avatar/{username}.jpeg" if username else "",
                    }
                except Exception:
                    pass

                # ============================================================
        # Data untuk card Current Upload (PREVIEW PRODUK)
        # Sumber: schedule.json dari folder project yang sedang diproses
        # Image path: schedule.json.product.id
        #   -> SELECT tiktok_id_product FROM tiktok_products WHERE id = product.id
        #   -> /static/products/<tiktok_id_product>/product/1.jpg
        # ============================================================
        current_job_data = None
        if self.current_schedule_data:
            product = self.current_schedule_data.get("product", {})
            sched = self.current_schedule_data.get("schedule", {})
            product_id = product.get("id", 0)

            # Query tiktok_id_product dari database
            tiktok_id_product = None
            if product_id:
                tiktok_id_product = get_tiktok_id_product(product_id)

            product_image = ""
            if tiktok_id_product:
                product_image = f"/static/products/{tiktok_id_product}/product/1.jpg"

            # Format tanggal jadwal
            schedule_dt = sched.get("datetime", "")
            schedule_display = ""
            if schedule_dt:
                try:
                    dt = datetime.strptime(schedule_dt, "%Y-%m-%d %H:%M:%S")
                    months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                              "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
                    schedule_display = f"{dt.day} {months[dt.month-1]} {dt.year} • {dt.strftime('%H:%M')}"
                except Exception:
                    schedule_display = schedule_dt

            current_job_data = {
                "product_title": product.get("title", ""),
                "product_image": product_image,
                "schedule_display": schedule_display,
            }

        return {

            "running": self.running,

            "progress": self.progress,

            "total_job": remaining,

            "logs": self.logs,

            # Upload Information Panel
            "info": {
                "creator": creator_info,
                "total_jobs": total_jobs,
                "success_count": success_count,
                "progress_persen": progress_persen,
                "upload_range_text": upload_range_text,
                "current_job": current_job_data,
            }

        }


manager = UploadManager()
