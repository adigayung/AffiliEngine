# File : includes/schedule/job.py

from datetime import datetime


class UploadJob:

    def __init__(
        self,
        job_id,
        batch_id,
        creator,
        product,
        schedule_datetime,
        video_filename,
        caption,
        llm_provider,
        llm_model
    ):

        self.job_id = job_id

        self.batch_id = batch_id

        self.creator = creator

        self.product = product

        self.schedule_datetime = schedule_datetime

        self.video_filename = video_filename

        self.caption = caption

        self.llm_provider = llm_provider

        self.llm_model = llm_model

    def to_json(self):

        return {

            "job_id": self.job_id,

            "batch_id": self.batch_id,

            "creator": {

                "id": self.creator["id"],

                "username": self.creator["username"]

            },

            "product": {

                "id": self.product["id"],

                "title": self.product["title"],

                "url": self.product["product_link"]

            },

            "schedule": {

                "datetime": self.schedule_datetime.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                "status": "pending"

            },

            "content": {

                "caption": self.caption

            },

            "files": {

                "video": self.video_filename,

                "thumbnail": "thumbnail.jpg"

            },

            "llm": {

                "provider": self.llm_provider,

                "model": self.llm_model,

                "generated_at": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            },

            "created_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        }