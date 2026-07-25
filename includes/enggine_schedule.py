# File : includes\enggine_schedule.py

import json, shutil, os, time
from flask import session
from pathlib import Path
from datetime import datetime, timedelta
from includes.upload_scheduler import create_upload_schedule
from includes.openrouter import LLM_OpenRouter

from includes.mysql import (
    get_creator,
    save_upload_job,
    get_product_basic,
    save_schedule_batch
)

from includes.config_loader import (
    get_app_config,
    get_openrouter_config
)

def upload_interval(request):

    creator_id = session.get("creator_id")
    app_config = get_app_config()
    openrouter_config = get_openrouter_config()
    current_creator = None

    if creator_id:

        current_creator = get_creator(creator_id)

    products = json.loads(request.form.get("products", "{}"))

    upload_directory = request.form.get("upload_directory")

    start_date = request.form.get("start_date")

    start_time = request.form.get("start_time")

    interval_hour = int(request.form.get("interval_hour", 20))

    schedule = create_upload_schedule(products)

    base_path = Path(upload_directory)

    base_path.mkdir(parents=True, exist_ok=True)

    total_duration = timedelta(
        hours=(len(schedule) - 1) * interval_hour
    )

    days = total_duration.days

    hours = total_duration.seconds // 3600

    duration_text = f"{days} Days {hours} Hours"

    current_time = datetime.strptime(
        f"{start_date} {start_time}",
        "%Y-%m-%d %H:%M"
    )

    created_folders = []

    start_datetime = current_time

    finish_datetime = start_datetime + timedelta(
        hours=(len(schedule) - 1) * interval_hour
    )

    batch_id = save_schedule_batch(
        creator_id=current_creator["id"],
        upload_directory=upload_directory,
        start_datetime=start_datetime,
        finish_datetime=finish_datetime,
        interval_hour=interval_hour,
        total_jobs=len(schedule)
    )

    for schedule_id, product_id in enumerate(schedule, start=1):

        folder_name = current_time.strftime("%Y_%m_%d_%H_%M")

        folder_path = base_path / folder_name

        folder_path.mkdir(exist_ok=True)

        product = get_product_basic(product_id)
        video_target_name = f"{folder_name}.mp4"
        with open(folder_path / video_target_name, "w", encoding="utf-8") as f:
            f.write("")

        job_id = save_upload_job(
            creator_id=current_creator["id"],
            batch_id=batch_id,
            product_id=product_id,
            schedule_datetime=current_time,
            folder=str(folder_path)
        )

        #################################################
        #       tulis deskripsi LLM
        #################################################
        prompt_file = os.path.join(
            "prompt",
            "description_caption.txt"
        )

        with open(
            prompt_file,
            "r",
            encoding="utf-8"
        ) as f:

            prompt_llm = f.read()

        prompt = prompt_llm.replace(
            "[[#PRODUCT_TITLE]]",
            product["title"]
        )

        prompt = prompt.replace(
            "[[#PRODUCT_TITLE]]",
            product["description"]
        )

        hasil_llm = LLM_OpenRouter(
            openrouter_config["models"]["tiktok_caption"],
            openrouter_config["api_key"],
            prompt,
            api_url=openrouter_config["base_url"],
            site_title=app_config["app_name"].replace(" ", "-")
        )
        hasil_llm = hasil_llm.replace("\r", "").replace("\n", " ")

        schedule_json = {

            "job_id": job_id,

            "batch_id": batch_id,

            "creator": {

                "id": current_creator["id"],
                "username": current_creator["username"]

            },

            "product": {

                "id": product_id,
                "title": product["title"],
                "url": product["product_link"]

            },

            "schedule": {

                "datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending"

            },

            "content": {

                "caption": hasil_llm

            },

            "files": {

                "video": video_target_name,
                "thumbnail": "thumbnail.jpg"

            },

            "llm": {

                "provider": "openrouter.ai",
                "model": openrouter_config["models"]["tiktok_caption"],
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },

            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        }

        with open(

            folder_path / "schedule.json",

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(
                schedule_json,
                f,
                indent=4,
                ensure_ascii=False
            )

        product_images = Path(f"static/products/{product_id}/product")

        user_data_source = os.path.join(
            "data",
            current_creator["username"]
        )
        
        shutil.copytree(
            user_data_source,
            folder_path / "aseets"
        )

        shutil.copytree(
            product_images,
            folder_path / "product"
        )

        #################################################
        #       tulis descripsi tiktok di product path 
        #################################################
        deskripsi_file = folder_path / "product" / "tiktok_description.txt"
        with open(deskripsi_file, "w", encoding="utf-8") as f:
            f.write(hasil_llm)

        #################################################
        #       tulis info product di product path 
        #################################################
        info_product = folder_path / "product" / "product.txt"
        string_info_product=f"""Creator : {current_creator["username"]}
Product ID : {product_id}
Title : {product["title"]}
Url : {product["product_link"]}
"""
        with open(info_product, "w", encoding="utf-8") as f:
            f.write(string_info_product)

        created_folders.append({

            "job_id": job_id,

            "batch_id": batch_id,

            "schedule_id": schedule_id,

            "product_id": product_id,

            "folder": str(folder_path),

            "datetime": current_time

        })

        current_time += timedelta(hours=interval_hour)

    batch_json = {

        "batch_id": batch_id,

        "creator": {

            "id": current_creator["id"],
            "username": current_creator["username"]

        },

        "schedule": {

            "start_datetime": start_datetime.strftime("%Y-%m-%d %H:%M:%S"),

            "finish_datetime": finish_datetime.strftime("%Y-%m-%d %H:%M:%S"),

            "interval_hour": interval_hour,

            "total_jobs": len(schedule),

            "status": "active"

        },

        "folders": [

            {

                "job_id": item["job_id"],

                "product_id": item["product_id"],

                "datetime": item["datetime"].strftime("%Y-%m-%d %H:%M:%S"),

                "path": item["folder"]

            }

            for item in created_folders

        ],

        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    }


    with open(
        base_path / "upload_schedule.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            batch_json,
            f,
            indent=4,
            ensure_ascii=False
        )
        
    return {

        "created_folders": created_folders,

        "products": products,

        "upload_directory": upload_directory,

        "start_date": start_date,

        "start_time": start_time,

        "interval_hour": interval_hour,

        "duration_text": duration_text,

    }
