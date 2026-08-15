# File : includes/schedule/scheduler.py
import json

from pathlib import Path

from datetime import datetime, timedelta

from flask import session

from includes.openrouter import LLM_OpenRouter

from includes.mysql import (
    get_creator,
    get_product_basic,
    save_upload_job,
    save_schedule_batch,
    get_shopee_affiliate_link
)

from includes.config_loader import (
    get_app_config,
    get_openrouter_config
)

from includes.schedule.algorithms import (
    create_upload_schedule
)

from includes.schedule.folder import (
    create_batch_folder,
    create_job_folder,
    create_empty_video,
    copy_creator_assets,
    copy_product_images,
    write_json,
    write_product_description,
    write_product_info
)

from includes.schedule.job import UploadJob

from includes.schedule.batch import UploadBatch


from includes.schedule.import_analyzer import generate_schedule_from_pattern, calculate_day_offset_from_pattern


class UploadScheduler:

    def __init__(self, request):

        self.request = request

        self.creator_id = session.get("creator_id")

        self.current_creator = None

        if self.creator_id:

            self.current_creator = get_creator(
                self.creator_id
            )

        self.app_config = get_app_config()

        self.openrouter_config = get_openrouter_config()

        self.products = json.loads(
            request.form.get(
                "products",
                "{}"
            )
        )

        self.upload_directory = request.form.get(
            "upload_directory"
        )

        self.start_date = request.form.get(
            "start_date"
        )

        self.start_time = request.form.get(
            "start_time"
        )

        self.interval_hour = int(
            request.form.get(
                "interval_hour",
                20
            )
        )

        self.interval_minute = int(
            request.form.get(
                "interval_minute",
                0
            )
        )


        print("========== REQUEST FORM ==========")

        for k, v in request.form.items():
            print(f"{k} = {repr(v)}")

        print("==================================")

        self.fixed_time_text = request.form.get(
            "fixed_time",
            ""
        )

        print("fixed_time =", repr(self.fixed_time_text))

        self.weekly_schedule = json.loads(
            request.form.get("weekly_schedule", "{}")
        )
        self.pattern_raw = request.form.get(
            "pattern"
        )

        self.import_pattern = request.form.get(
            "import_pattern",
            "{}"
        )

        self.import_times = request.form.get(
            "import_times",
            "[]"
        )

        self.import_daily_schedule = request.form.get(
            "import_daily_schedule",
            "[]"
        )

        self.path_list = request.form.get(
            "path_list",
            ""
        ).splitlines()

        self.schedule = []

        self.created_folders = []

        self.batch_id = None

        self.batch_folder = None

        self.base_path = Path(
            self.upload_directory
        )

        self.current_time = None

        self.start_datetime = None

        self.finish_datetime = None

        self.duration_text = ""

    def process_jobs(self):

        for schedule_id, product_id in enumerate(
            self.schedule,
            start=1
        ):

            product = get_product_basic(
                product_id
            )

            folder_path = create_job_folder(
                self.batch_folder,
                self.current_time
            )

            video_filename = (
                self.current_time.strftime(
                    "%Y_%m_%d_%H_%M"
                ) + ".mp4"
            )

            create_empty_video(
                folder_path,
                video_filename
            )

            caption = self.generate_caption(
                product
            )
            #caption = "LLM masih kosong"
            job_id = save_upload_job(
                creator_id=self.current_creator["id"],
                batch_id=self.batch_id,
                product_id=product_id,
                schedule_datetime=self.current_time,
                folder=str(folder_path)
            )

            self.create_job_files(
                folder_path=folder_path,
                product=product,
                job_id=job_id,
                video_filename=video_filename,
                caption=caption
            )

            self.created_folders.append({

                "job_id": job_id,

                "batch_id": self.batch_id,

                "schedule_id": schedule_id,

                "product_id": product_id,

                "folder": str(folder_path),

                "datetime": self.current_time

            })

            self.current_time += timedelta(
                hours=self.interval_hour
            )


    def generate_caption(self, product):
        #return "manuk"
        prompt_file = Path(
            "prompt"
        ) / "description_caption.txt"

        with open(
            prompt_file,
            "r",
            encoding="utf-8"
        ) as f:

            prompt = f.read()

        prompt = prompt.replace(
            "[[#PRODUCT_TITLE]]",
            product["title"]
        )

        prompt = prompt.replace(
            "[[#PRODUCT_DESCRIPTION]]",
            product["description"]
        )

        hasil = LLM_OpenRouter(

            self.openrouter_config["models"]["tiktok_caption"],

            self.openrouter_config["api_key"],

            prompt,

            api_url=self.openrouter_config["base_url"],

            site_title=self.app_config["app_name"].replace(
                " ",
                "-"
            )

        )

        return hasil.replace(
            "\r",
            ""
        ).replace(
            "\n",
            " "
        ).strip()
    
    def create_job_files(

        self,

        folder_path,

        product,

        job_id,

        video_filename,

        caption

    ):

        # Additive: lookup Shopee Affiliate (None jika tidak ada mapping)
        shopee_affiliate_link = get_shopee_affiliate_link(
            product["tiktok_id_product"]
        )

        job = UploadJob(

            job_id=job_id,

            batch_id=self.batch_id,

            creator=self.current_creator,

            product=product,

            schedule_datetime=self.current_time,

            video_filename=video_filename,

            caption=caption,

            llm_provider="openrouter.ai",

            llm_model=self.openrouter_config["models"]["tiktok_caption"],

            shopee_affiliate_link=shopee_affiliate_link

        )

        write_json(

            folder_path / "schedule.json",

            job.to_json()

        )

        copy_creator_assets(

            self.current_creator["username"],

            folder_path

        )

        copy_product_images(

            product["tiktok_id_product"],

            folder_path

        )
        print(folder_path)
        print((folder_path / "product").exists())
        write_product_description(
            folder_path,
            caption
        )

        write_product_info(

            folder_path,

            self.current_creator["username"],

            product

        )


    def prepare_time_interval(self):

        self.current_time = datetime.strptime(
            f"{self.start_date} {self.start_time}",
            "%Y-%m-%d %H:%M"
        )

        self.start_datetime = self.current_time

        self.finish_datetime = (
            self.start_datetime +
            timedelta(
                hours=(len(self.schedule) - 1) *
                self.interval_hour
            )
        )

        total_duration = (
            self.finish_datetime -
            self.start_datetime
        )

        days = total_duration.days

        hours = total_duration.seconds // 3600

        self.duration_text = (
            f"{days} Days {hours} Hours"
        )

    def prepare_time_fixed(self):

        upload_times = json.loads(
            self.request.form.get(
                "upload_times",
                "[]"
            )
        )

        if not upload_times:

            raise ValueError(
                "Upload time kosong."
            )

        upload_times.sort()

        start_date = datetime.strptime(
            self.start_date,
            "%Y-%m-%d"
        )

        first_hour, first_minute = map(
            int,
            upload_times[0].split(":")
        )

        self.start_datetime = datetime(
            start_date.year,
            start_date.month,
            start_date.day,
            first_hour,
            first_minute
        )

        total_day = (
            len(self.schedule) - 1
        ) // len(upload_times)

        last_slot = (
            len(self.schedule) - 1
        ) % len(upload_times)

        last_hour, last_minute = map(
            int,
            upload_times[last_slot].split(":")
        )

        self.finish_datetime = datetime(
            start_date.year,
            start_date.month,
            start_date.day,
            last_hour,
            last_minute
        ) + timedelta(
            days=total_day
        )

        total_duration = (
            self.finish_datetime -
            self.start_datetime
        )

        days = total_duration.days

        hours = total_duration.seconds // 3600

        self.duration_text = (
            f"{days} Days {hours} Hours"
        )

    def prepare_time_weekly(self):

        self.current_time = datetime.strptime(
            f"{self.start_date} 00:00",
            "%Y-%m-%d %H:%M"
        )

        self.start_datetime = self.current_time

        self.finish_datetime = self.current_time

        self.duration_text = ""
		
    def prepare_time_pattern(self):

        self.current_time = datetime.strptime(
            f"{self.start_date} 00:00",
            "%Y-%m-%d %H:%M"
        )

        self.start_datetime = self.current_time

        self.finish_datetime = self.current_time

        self.duration_text = ""

    def interval(self):

        self.prepare_time = (
            self.prepare_time_interval
        )

        self.prepare()

        self.process_jobs()

        self.finish()

        return self.result()
		
    def fixed_time(self):

        self.prepare_time = (
            self.prepare_time_fixed
        )

        self.prepare()

        self.process_fixed_time_jobs()

        self.finish()

        return self.result()
		
    def weekly(self, weekly_schedule):

        self.prepare_time = self.prepare_time_weekly

        self.weekly_schedule = weekly_schedule

        self.prepare()

        self.process_weekly_jobs()

        self.finish()

        return self.result()
		
    def pattern(self):

        self.prepare_time = (
            self.prepare_time_pattern
        )

        self.prepare()

        self.process_pattern_jobs()

        self.finish()

        return self.result()

    def import_schedule(self):

        self.prepare_time = (
            self.prepare_time_pattern
        )

        self.prepare()

        self.process_import_jobs()

        self.finish()

        return self.result()

    def prepare(self):

        self.base_path.mkdir(
            parents=True,
            exist_ok=True
        )

        self.schedule = create_upload_schedule(
            self.products
        )

        # hitung waktu sesuai mode scheduler
        self.prepare_time()

        self.batch_folder = create_batch_folder(
            self.upload_directory,
            self.start_datetime
        )

        self.batch_id = save_schedule_batch(
            creator_id=self.current_creator["id"],
            upload_directory=str(self.batch_folder),
            start_datetime=self.start_datetime,
            finish_datetime=self.finish_datetime,
            interval_hour=self.interval_hour,
            total_jobs=len(self.schedule)
        )

    def process_interval_jobs():
        pass

    def process_fixed_time_jobs(self):

        upload_times = json.loads(
            self.request.form.get(
                "upload_times",
                "[]"
            )
        )

        if not upload_times:

            raise ValueError(
                "Upload time kosong."
            )

        upload_times.sort()

        start_date = datetime.strptime(
            self.start_date,
            "%Y-%m-%d"
        )

        for schedule_id, product_id in enumerate(
            self.schedule,
            start=1
        ):

            slot = (schedule_id - 1) % len(upload_times)

            day = (schedule_id - 1) // len(upload_times)

            hour, minute = map(
                int,
                upload_times[slot].split(":")
            )

            self.current_time = datetime(
                start_date.year,
                start_date.month,
                start_date.day,
                hour,
                minute
            ) + timedelta(
                days=day
            )

            product = get_product_basic(
                product_id
            )

            folder_path = create_job_folder(
                self.batch_folder,
                self.current_time
            )

            video_filename = (
                self.current_time.strftime(
                    "%Y_%m_%d_%H_%M"
                ) + ".mp4"
            )

            create_empty_video(
                folder_path,
                video_filename
            )

            caption = self.generate_caption(
                product
            )
            #caption = "LLM masih kosong"
            job_id = save_upload_job(
                creator_id=self.current_creator["id"],
                batch_id=self.batch_id,
                product_id=product_id,
                schedule_datetime=self.current_time,
                folder=str(folder_path)
            )

            self.create_job_files(
                folder_path=folder_path,
                product=product,
                job_id=job_id,
                video_filename=video_filename,
                caption=caption
            )

            self.created_folders.append({

                "job_id": job_id,

                "batch_id": self.batch_id,

                "schedule_id": schedule_id,

                "product_id": product_id,

                "folder": str(folder_path),

                "datetime": self.current_time

            })

    def process_weekly_jobs(self):

        upload_times = []

        for day, times in self.weekly_schedule.items():
            for t in times:
                upload_times.append({
                    "day": day,
                    "time": t
                })

        if not upload_times:
            raise ValueError(
                "Weekly upload time kosong."
            )

        current_date = datetime.strptime(
            self.start_date,
            "%Y-%m-%d"
        )

        product_index = 0
        total_products = len(self.schedule)

        while product_index < total_products:

            day_name = current_date.strftime("%A")

            day_times = self.weekly_schedule.get(
                day_name,
                []
            )

            if not day_times:
                current_date += timedelta(days=1)
                continue

            # Urutkan waktu ascending
            day_times_sorted = sorted(day_times)

            # Proses semua slot waktu pada hari ini
            for time_str in day_times_sorted:

                if product_index >= total_products:
                    break

                hour, minute = map(
                    int,
                    time_str.split(":")
                )

                self.current_time = datetime(
                    current_date.year,
                    current_date.month,
                    current_date.day,
                    hour,
                    minute
                )

                product_id = self.schedule[product_index]
                product_index += 1

                product = get_product_basic(product_id)

                folder_path = create_job_folder(
                    self.batch_folder,
                    self.current_time
                )

                video_filename = (
                    self.current_time.strftime(
                        "%Y_%m_%d_%H_%M"
                    ) + ".mp4"
                )

                create_empty_video(folder_path, video_filename)
                caption = self.generate_caption(
                    product
                )
                #caption = "LLM masih kosong"

                job_id = save_upload_job(
                    creator_id=self.current_creator["id"],
                    batch_id=self.batch_id,
                    product_id=product_id,
                    schedule_datetime=self.current_time,
                    folder=str(folder_path)
                )

                self.create_job_files(
                    folder_path=folder_path,
                    product=product,
                    job_id=job_id,
                    video_filename=video_filename,
                    caption=caption
                )

                self.created_folders.append({
                    "job_id": job_id,
                    "batch_id": self.batch_id,
                    "schedule_id": product_index,
                    "product_id": product_id,
                    "folder": str(folder_path),
                    "datetime": self.current_time
                })

            # Lanjut ke hari berikutnya
            current_date += timedelta(days=1)

    def process_pattern_jobs(self):

        pattern_data = json.loads(self.pattern_raw)

        if not pattern_data:

            raise ValueError(
                "Pattern data kosong."
            )

        start_date = datetime.strptime(
            self.start_date,
            "%Y-%m-%d"
        )

        total_products = len(self.schedule)
        schedule_index = 0

        # current_stage_date tracks where this stage begins
        current_stage_date = start_date

        # -------------------------------------------------------
        # 1) Run all stages EXCEPT the last one, each once
        # -------------------------------------------------------
        for stage_idx, stage in enumerate(pattern_data[:-1]):

            strategy = stage.get("strategy")
            unit = stage.get("unit", "days")
            duration = stage.get("duration")
            config = stage.get("config", {})

            if duration is None:
                continue

            duration_days = self._pattern_unit_to_days(duration, unit)

            # Calculate how many products fit in this stage's window
            stage_product_count = self._pattern_calc_product_count(
                strategy, duration_days, config, current_stage_date
            )

            if stage_product_count <= 0:
                continue

            # Limit to remaining products
            stage_product_count = min(
                stage_product_count,
                total_products - schedule_index
            )

            if stage_product_count <= 0:
                continue

            # Extract products for this stage
            stage_product_ids = self.schedule[
                schedule_index:schedule_index + stage_product_count
            ]

            self._pattern_run_stage(
                strategy, stage_product_ids, current_stage_date, config
            )

            schedule_index += stage_product_count

            # Move to the day after this stage's last job
            current_stage_date = (
                self.current_time + timedelta(days=1)
            ).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            if schedule_index >= total_products:
                return

        # -------------------------------------------------------
        # 2) Run the LAST stage repeatedly until all videos done
        # -------------------------------------------------------
        last_stage = pattern_data[-1]
        last_strategy = last_stage.get("strategy")
        last_config = last_stage.get("config", {})

        while schedule_index < total_products:

            # Calculate how many products fit in one iteration
            # For weekly: use 7 days window
            # For interval/fixed: use 1 day window per iteration
            if last_strategy == "weekly":
                iteration_days = 7
            else:
                iteration_days = 1

            stage_product_count = self._pattern_calc_product_count(
                last_strategy, iteration_days, last_config,
                current_stage_date
            )

            # Fallback: at least 1 product per iteration
            if stage_product_count <= 0:
                stage_product_count = 1

            stage_product_count = min(
                stage_product_count,
                total_products - schedule_index
            )

            if stage_product_count <= 0:
                break

            stage_product_ids = self.schedule[
                schedule_index:schedule_index + stage_product_count
            ]

            self._pattern_run_stage(
                last_strategy, stage_product_ids,
                current_stage_date, last_config
            )

            schedule_index += stage_product_count

            # Advance to next iteration window
            if last_strategy == "weekly":
                current_stage_date += timedelta(weeks=1)
            else:
                current_stage_date = (
                    self.current_time + timedelta(days=1)
                ).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

    def _pattern_calc_product_count(
        self, strategy, duration_days, config, start_date
    ):

        if strategy == "interval":
            interval_hour = config.get("interval_hour", 24)
            if interval_hour <= 0:
                interval_hour = 24
            products_per_day = 24 // interval_hour
            if products_per_day < 1:
                products_per_day = 1
            max_products = duration_days * products_per_day

        elif strategy in ("fixed", "fixed_time"):
            times = config.get("times", [])
            if not times:
                return 0
            products_per_day = len(times)
            max_products = duration_days * products_per_day

        elif strategy == "weekly":
            max_products = 0
            for day_offset in range(duration_days):
                day_name = (
                    start_date + timedelta(days=day_offset)
                ).strftime("%A")
                day_times = config.get(day_name, [])
                max_products += len(day_times)

        else:
            max_products = 0

        return max_products

    def process_import_jobs(self):
        """
        Memproses jadwal berdasarkan hasil Pattern Editor dari Import Schedule.

        Flow:
        1. Terima data pattern yang sudah diedit user dari UI (initial_pattern + repeat_pattern)
        2. Generate daftar waktu upload berdasarkan pola harian
        3. Assign setiap waktu ke produk secara berurutan
        """
        import_data = json.loads(self.import_pattern)
        # Fallback times (jika ada)
        fallback_times = json.loads(self.import_times)

        total_products = len(self.schedule)

        # ==============================
        # GENERATE SCHEDULE TIMES
        # ==============================
        schedule_times = generate_schedule_from_pattern(
            import_data,
            total_products,
            fallback_times
        )

        # ==============================
        # AMBIL START DATE
        # ==============================
        start_date = datetime.strptime(
            self.start_date,
            "%Y-%m-%d"
        )

        # ==============================
        # PROSES SETIAP PRODUK
        # ==============================
        for schedule_id, product_id in enumerate(
            self.schedule,
            start=1
        ):

            time_str = schedule_times[schedule_id - 1]
            hour, minute = map(int, time_str.split(":"))

            product_idx = schedule_id - 1
            day_offset = calculate_day_offset_from_pattern(import_data, product_idx)

            self.current_time = datetime(
                start_date.year,
                start_date.month,
                start_date.day,
                hour,
                minute
            ) + timedelta(days=day_offset)

            self._create_job_entry(schedule_id, product_id)

    def _pattern_run_stage(
        self, strategy, product_ids, start_date, config
    ):

        if strategy == "interval":
            self._pattern_process_interval(
                product_ids, start_date, config
            )

        elif strategy in ("fixed", "fixed_time"):
            times = config.get("times", [])
            if not times:
                raise ValueError(
                    "Fixed time config kosong."
                )
            self._pattern_process_fixed(
                product_ids, start_date, times
            )

        elif strategy == "weekly":
            day_keys = [
                "Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday"
            ]
            schedule_config = {}
            for d in day_keys:
                schedule_config[d] = config.get(d, [])
            self._pattern_process_weekly(
                product_ids, start_date, schedule_config
            )

        else:
            raise ValueError(
                f"Unknown strategy '{strategy}'."
            )

    def _pattern_unit_to_days(self, duration, unit):

        try:
            duration = int(duration)
        except (ValueError, TypeError):
            duration = 0

        if unit == "days":
            return duration
        elif unit == "weeks":
            return duration * 7
        elif unit == "months":
            return duration * 30
        return duration

    def _pattern_process_interval(
        self, product_ids, start_date, config
    ):

        interval_hour = config.get("interval_hour", 24)
        interval_minute = config.get("interval_minute", 0)

        for schedule_id, product_id in enumerate(
            product_ids, start=1
        ):

            hours_offset = (schedule_id - 1) * interval_hour
            minutes_offset = (schedule_id - 1) * interval_minute

            self.current_time = datetime(
                start_date.year,
                start_date.month,
                start_date.day
            ) + timedelta(
                hours=hours_offset + start_date.hour,
                minutes=minutes_offset + start_date.minute
            )

            self._create_job_entry(schedule_id, product_id)

    def _pattern_process_fixed(
        self, product_ids, start_date, times
    ):

        times.sort()

        for schedule_id, product_id in enumerate(
            product_ids, start=1
        ):

            slot = (schedule_id - 1) % len(times)
            day = (schedule_id - 1) // len(times)

            hour, minute = map(int, times[slot].split(":"))

            self.current_time = datetime(
                start_date.year,
                start_date.month,
                start_date.day,
                hour,
                minute
            ) + timedelta(days=day)

            self._create_job_entry(schedule_id, product_id)

    def _pattern_process_weekly(
        self, product_ids, start_date, schedule_config
    ):

        current_date = start_date
        product_index = 0
        total_products = len(product_ids)

        while product_index < total_products:

            day_name = current_date.strftime("%A")
            day_times = schedule_config.get(day_name, [])

            if not day_times:
                current_date += timedelta(days=1)
                continue

            # Urutkan waktu ascending
            day_times_sorted = sorted(day_times)

            for time_str in day_times_sorted:

                if product_index >= total_products:
                    break

                hour, minute = map(
                    int, time_str.split(":")
                )

                self.current_time = datetime(
                    current_date.year,
                    current_date.month,
                    current_date.day,
                    hour,
                    minute
                )

                product_id = product_ids[product_index]
                product_index += 1

                self._create_job_entry(product_index, product_id)

            current_date += timedelta(days=1)

    def _create_job_entry(self, schedule_id, product_id):

        product = get_product_basic(product_id)

        folder_path = create_job_folder(
            self.batch_folder,
            self.current_time
        )

        video_filename = (
            self.current_time.strftime("%Y_%m_%d_%H_%M") + ".mp4"
        )

        create_empty_video(folder_path, video_filename)

        caption = self.generate_caption(product)
        #caption = "LLM masih kosong"
        job_id = save_upload_job(
            creator_id=self.current_creator["id"],
            batch_id=self.batch_id,
            product_id=product_id,
            schedule_datetime=self.current_time,
            folder=str(folder_path)
        )

        self.create_job_files(
            folder_path=folder_path,
            product=product,
            job_id=job_id,
            video_filename=video_filename,
            caption=caption
        )

        self.created_folders.append({
            "job_id": job_id,
            "batch_id": self.batch_id,
            "schedule_id": schedule_id,
            "product_id": product_id,
            "folder": str(folder_path),
            "datetime": self.current_time
        })

    def finish(self):

        batch = UploadBatch(

            batch_id=self.batch_id,

            creator=self.current_creator,

            start_datetime=self.start_datetime,

            finish_datetime=self.finish_datetime,

            interval_hour=self.interval_hour,

            created_folders=self.created_folders

        )

        write_json(

            self.batch_folder / "upload_schedule.json",

            batch.to_json()

        )

    def result(self):

        return {

            "created_folders": self.created_folders,

            "products": self.products,

            "upload_directory": str(self.batch_folder),

            "start_date": self.start_date,

            "start_time": self.start_time,

            "interval_hour": self.interval_hour,

            "duration_text": self.duration_text,

            "batch_id": self.batch_id

        }
