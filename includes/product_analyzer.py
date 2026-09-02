# includes/product_analyzer.py
import json
import os
import shutil
import time
from datetime import datetime

from includes.mysql import (
    save_product,
    save_product_analysis,
    save_llm_analysis
)

from includes.ocr_img_to_text_ss import OCRProcessor

from includes.opportunity import calculate_opportunity

from includes.normalisasi_ocr import parse_ocr, str_k_to_int
from includes.remove_all_file import clear_files_in_path

from includes.request_tt import get_info_tt_from_url

from includes.openrouter import LLM_OpenRouter

from includes.config_loader import get_app_config, get_openrouter_config

from includes.logFX import logger

from includes.utils import (
    clear_files_in_path,
    safe_price,
    safe_float,
    safe_int    
)


def analyze_product(
    image,
    product_link,
    enable_llm=True,
    upload_folder="upload",
    raw_data=None
):
    """
    Analisa produk TikTok Affiliate.

    Parameters
    ----------
    image : werkzeug.datastructures.FileStorage
        File upload dari Flask.

    product_link : str
        Link produk TikTok.

    enable_llm : bool
        True = lakukan analisa LLM.

    upload_folder : str
        Folder upload sementara.

    raw_data : dict | None
        Metrik TikTok yang diinput manual (jalur NON-OCR):
        {"komisi", "persentase_komisi", "rating", "pesanan",
         "ctr", "kreator", "keranjang"}.
        Bila None -> metrik diambil dari OCR screenshot (behavior lama).
        Bila dict  -> proses OCR dilewati sepenuhnya, namun data produk
        (title/description/price/vote/sold) tetap di-scrape via
        get_info_tt_from_url().

    Returns
    -------
    dict
    """

    extracted_data = {}
    hasil_llm = ""
    start_time = time.time()

    ############################################################
    # Ambil data dasar produk (SELALU via URL scraper)
    ############################################################

    data_dasar = get_info_tt_from_url(
        product_link,
        "./chromium"
    )

    if not data_dasar:
        raise Exception(
            "Gagal mengambil data produk dari URL. "
            "Pastikan URL produk valid dan dapat diakses."
        )

    ############################################################
    # Sumber metrik TikTok: OCR screenshot ATAU input manual
    ############################################################

    if raw_data is not None:

        # Jalur input manual: metrik TikTok berasal dari form,
        # proses OCR dilewati sepenuhnya.
        raw = raw_data

    else:

        # Jalur OCR (behavior existing)

        if image is None:
            raise Exception("Image is None")

        if isinstance(image, str):

            filepath = image

        # image berupa FileStorage (request.files["image"])
        else:
            ext = os.path.splitext(image.filename)[1]
            filepath = os.path.join(
                upload_folder,
                data_dasar.get("tiktok_id_product", "temp") + ext
            )
            image.save(filepath)

        debug_folder = os.path.join(
            "debug",
            "products",
            data_dasar.get("tiktok_id_product", "")
        )

        os.makedirs(
            debug_folder,
            exist_ok=True
        )

        ss_file = os.path.join(
            debug_folder,
            datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            + os.path.splitext(filepath)[1]
        )

        shutil.copy2(
            filepath,
            ss_file
        )

        ############################################################
        # OCR
        ############################################################

        #processor = OCRProcessor()
        processor = OCRProcessor(data_dasar.get("tiktok_id_product", "tanpa_id"))

        raw_ocr_text = processor.run(filepath)
        logger("info", "====================xxxxxxxxxxxxxxxxx=============================")
        raw = parse_ocr(raw_ocr_text)

    if raw.get("persentase_komisi") and raw.get("komisi"):

        persentase = float(raw["persentase_komisi"])
        komisi = float(raw["komisi"])

        if persentase > 0:
            price_baru = int(
                komisi / (persentase / 100)
            )
        else:
            price_baru = safe_price(
                data_dasar.get("price", 0)
            )

    else:

        price_baru = safe_price(
            data_dasar.get("price", 0)
        )

    logger("info", raw)
    # raw = parse_tiktok_analytics(filepath)

    ############################################################
    # Build extracted data
    ############################################################

    extracted_data = {

        "tiktok_id_product":
            data_dasar.get("tiktok_id_product", "") or "",

        "title":
            data_dasar.get("title", "") or "",

        "description":
            data_dasar.get("description", "") or "",

        "price":
            price_baru,

        "rating":
            safe_float(
                raw.get("rating") or data_dasar.get("rating") or 0
            ),

        "vote":
            safe_int(
                str_k_to_int(
                    data_dasar.get("vote", 0)
                )
            ),

        "sold":
            safe_int(
                str_k_to_int(
                    data_dasar.get("sold", 0)
                )
            ),

        "product_link":
            product_link,

        "komisi":
            safe_float(raw.get("komisi", 0)),

        "stok_tersedia":
            safe_int(raw.get("stok", 0)),

        "ulasan_positif":
            safe_float(raw.get("ulasan", 0)),

        "pesanan":
            safe_int(raw.get("pesanan", 0)),

        "ctr":
            safe_float(
                str(
                    raw.get("ctr") or 0
                ).replace(",", ".")
            ),

        "jumlah_kreator":
            safe_int(
                raw.get("kreator", 1)
            ),

        "pembeli_keranjang":
            safe_int(
                raw.get("keranjang", 0)
            ),
    }

    logger(
        "debug",
        extracted_data
    )

    # Jalur input manual: persentase_komisi wajib diteruskan ke
    # opportunity engine (commission.py membaca data["persentase_komisi"]).
    # Jalur OCR tidak menyertakan field ini agar behavior existing
    # /analyze-by-phone tidak berubah.
    if raw_data is not None:
        extracted_data["persentase_komisi"] = safe_float(
            raw_data.get("persentase_komisi", 0)
        )

    ############################################################
    # Opportunity Engine
    ############################################################

    analysis = calculate_opportunity(
        extracted_data
    )

    ############################################################
    # Bersihkan folder upload
    ############################################################

    for filename in os.listdir(upload_folder):

        file_path = os.path.join(
            upload_folder,
            filename
        )

        #if os.path.isfile(file_path):
        #    os.remove(file_path)

    ############################################################
    # Analisa LLM
    ############################################################

    if enable_llm:

        logger(
            "info",
            "Memulai analisa LLM..."
        )

        app_config = get_app_config()

        openrouter_config = get_openrouter_config()

        prompt_file = os.path.join(
            "prompt",
            "analisa_LLM.txt"
        )

        with open(
            prompt_file,
            "r",
            encoding="utf-8"
        ) as f:

            prompt_llm = f.read()

        prompt_llm = prompt_llm.replace(
            "[[#PRODUCT_DATA]]",
            json.dumps(
                extracted_data,
                indent=2,
                ensure_ascii=False
            )
        )

        prompt_llm = prompt_llm.replace(
            "[[#ANALYSIS_DATA]]",
            json.dumps(
                analysis,
                indent=2,
                ensure_ascii=False
            )
        )

        hasil_llm = LLM_OpenRouter(
            openrouter_config["models"]["text_analysis"],
            openrouter_config["api_key"],
            prompt_llm,
            api_url=openrouter_config["base_url"],
            site_title=app_config["app_name"].replace(
                " ",
                "-"
            )
        )

        logger(
            "info",
            "Hasil LLM : " + hasil_llm
        )

    ############################################################
    # Simpan Database
    ############################################################

    logger("debug", "-----------------------------------")
    logger("debug", analysis)

    product_id = save_product(
        extracted_data
    )

    analysis_id = save_product_analysis(
        product_id,
        analysis
    )

    if enable_llm:

        save_llm_analysis(
            product_id=product_id,
            analysis_id=analysis_id,
            provider="OpenRouter",
            model=openrouter_config["models"]["text_analysis"],
            llm_analysis=hasil_llm
        )

    #clear_files_in_path("./temp")
    #clear_files_in_path(upload_folder)

    ############################################################
    # Return
    ############################################################
    waktu_proses = time.time() - start_time

    if waktu_proses >= 60:
        menit = int(waktu_proses // 60)
        detik = waktu_proses % 60
        logger("info", f"Selesai dalam {menit} menit {detik:.1f} detik")
    else:
        logger("info", f"Selesai dalam {waktu_proses:.1f} detik")

    return {

        "product_id": product_id,

        "analysis_id": analysis_id,

        "product": extracted_data,

        "analysis": analysis,

        "hasil_llm": hasil_llm,

    }