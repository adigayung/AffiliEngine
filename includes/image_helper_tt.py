import os
import requests
from PIL import Image
from io import BytesIO
from includes.logFX import logger

def download_product_images(images, tiktok_product_id):

    """
    Download semua gambar produk ke:
    static/products/{tiktok_product_id}/product/
    """

    product_folder = os.path.join(
        "static",
        "products",
        str(tiktok_product_id),
        "product"
    )

    os.makedirs(product_folder, exist_ok=True)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"
        )
    }

    total = 0

    for index, image in enumerate(images, start=1):

        url_list = image.get("url_list", [])

        if not url_list:
            continue

        image_url = url_list[0].replace("\\u002F", "/")

        save_path = os.path.join(
            product_folder,
            f"{index}.jpg"
        )

        try:

            response = requests.get(
                image_url,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:


                img = Image.open(BytesIO(response.content))

                img = img.convert("RGB")

                img.save(save_path, "JPEG", quality=95)

                # with open(save_path, "wb") as f:
                #     f.write(response.content)

                logger("debug", f"IMAGE {index} SAVED")

                total += 1

            else:

                logger(
                    "error",
                    f"DOWNLOAD IMAGE {index} FAILED ({response.status_code})"
                )

        except Exception as e:

            logger(
                "error",
                f"DOWNLOAD IMAGE {index} ERROR : {e}"
            )

    logger("debug", f"TOTAL IMAGE : {total}")

    return total