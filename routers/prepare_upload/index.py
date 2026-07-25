import os
import shutil
import time

from flask import (
    render_template,
    request,
    Blueprint
)
from includes.logFX import logger
from includes.request_tt import get_info_tt_from_url
from includes.openrouter import LLM_OpenRouter
from includes.config_loader import (
    get_app_config,
    get_openrouter_config
)


prepare_upload_bp = Blueprint(
    "prepare_upload",
    __name__,
    url_prefix="/prepare_upload"
)


@prepare_upload_bp.route("/", methods=["GET", "POST"])
def index():

    hasil_llm = None
    product = None

    if request.method == "POST":

        path = request.form.get("path", "").strip()

        logger("debug", f"Prepare Path : {path}")

        # =====================================================
        # VALIDATE PATH
        # =====================================================

        if os.path.isdir(path):

            url_file = os.path.join(path, "url.txt")

            if os.path.isfile(url_file):

                with open(url_file, "r", encoding="utf-8") as f:

                    url = f.read().strip()

                logger("info", f"URL : {url}")

                # ===============================================
                # GET PRODUCT INFO
                # ===============================================

                product = get_info_tt_from_url(url, "./chromium")

                if product:
                    ss_path_source = os.path.join(
                                        "static",
                                        "products",
                                        product["tiktok_id_product"],
                                        "product"
                                     )
                    ss_path_destination = os.path.join(
                                            path,
                                            "product_images"
                                          )

                    logger("info", "prosess copy image product.")
                    shutil.copytree(ss_path_source, ss_path_destination)
                    
                    start = time.perf_counter()
                    app_config = get_app_config()
                    openrouter_config = get_openrouter_config()

                    # ===========================================
                    # BUILD PROMPT
                    # ===========================================

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

                    logger("info", "prompt : " + prompt)
                    # ===========================================
                    # CALL LLM
                    # ===========================================
                    logger("info", "Caption generated.")
                    logger("info", "Tunggu Sebentar, Memulai....")
                    hasil_llm = LLM_OpenRouter(
                        openrouter_config["models"]["tiktok_caption"],
                        openrouter_config["api_key"],
                        prompt,
                        api_url=openrouter_config["base_url"],
                        site_title=app_config["app_name"].replace(" ", "-")
                    )
                    elapsed = time.perf_counter() - start
                    
                    hasil_llm = hasil_llm.replace("\r", "").replace("\n", " ")
                    deskripsi_file = os.path.join(
                                        path,
                                        "tiktok_description.txt"
                                     )
                    with open(deskripsi_file, "w", encoding="utf-8") as f:
                        f.write(hasil_llm)
                    logger("info", "Hasil LLM : " + hasil_llm)

                    if elapsed < 60:
                        logger("info", f"Selesai dalam {elapsed:.2f} detik")
                    else:
                        menit = int(elapsed // 60)
                        detik = elapsed % 60
                        logger("info", f"Selesai dalam {menit} menit {detik:.2f} detik")
    
            else:

                logger("error", "url.txt not found.")

        else:

            logger("error", "Invalid folder.")

    return render_template(
        "prepare_upload/index.html",
        product=product,
        hasil_llm=hasil_llm
    )