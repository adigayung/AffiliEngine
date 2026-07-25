# File : includes/schedule/batch.py

from datetime import datetime


class UploadBatch:

    def __init__(
        self,
        batch_id,
        creator,
        start_datetime,
        finish_datetime,
        interval_hour,
        created_folders
    ):

        self.batch_id = batch_id

        self.creator = creator

        self.start_datetime = start_datetime

        self.finish_datetime = finish_datetime

        self.interval_hour = interval_hour

        self.created_folders = created_folders

    def to_json(self):

        return {

            "batch_id": self.batch_id,

            "creator": {

                "id": self.creator["id"],

                "username": self.creator["username"]

            },

            "schedule": {

                "start_datetime": self.start_datetime.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                "finish_datetime": self.finish_datetime.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                "interval_hour": self.interval_hour,

                "total_jobs": len(self.created_folders),

                "status": "active"

            },

            "folders": [

                {

                    "job_id": item["job_id"],

                    "batch_id": item["batch_id"],

                    "schedule_id": item["schedule_id"],

                    "product_id": item["product_id"],

                    "datetime": item["datetime"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                    "path": item["folder"]

                }

                for item in self.created_folders

            ],

            "created_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        }