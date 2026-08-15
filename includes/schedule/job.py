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
        llm_model,
        shopee_affiliate_link=None
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

        # Additive: Shopee Affiliate (None jika produk tidak punya mapping)
        self.shopee_affiliate_link = shopee_affiliate_link

    def to_json(self):

        schedule_datetime_str = self.schedule_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

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

                "url": self.product["product_link"],

                # Additive: Shopee Affiliate link (None jika tidak ada mapping)
                "shopee_affiliate_link": self.shopee_affiliate_link

            },

            "schedule": {

                "datetime": schedule_datetime_str,

                "status": "pending"

            },

            # Additive: Facebook mengikuti jadwal TikTok 100% sama.
            # status = "pending" jika ada mapping Shopee,
            #          "not_available" jika tidak ada mapping Shopee.
            "facebook_schedule": {

                "datetime": schedule_datetime_str,

                "status": (
                    "pending"
                    if self.shopee_affiliate_link
                    else "not_available"
                )

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
