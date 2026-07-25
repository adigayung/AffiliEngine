import os
import shutil
import json
from includes.logFX import logger

def clear_files_in_path(path: str) -> None:
    """
    Menghapus seluruh isi folder (file dan subfolder),
    tetapi folder utamanya tetap dipertahankan.
    """

    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        return

    for name in os.listdir(path):
        item = os.path.join(path, name)

        try:
            if os.path.isfile(item) or os.path.islink(item):
                os.remove(item)

                logger(
                    "info",
                    f"menghapus : {item}"
                )
            elif os.path.isdir(item):
                shutil.rmtree(item)
        except Exception as e:
            logger(
                "error",
                f"Gagal menghapus {item}: {e}"
            )

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        value = str(value).strip()

        if value == "":
            return default

        return float(value)

    except:
        return default


def safe_int(value, default=0):
    try:
        if value is None:
            return default

        value = str(value).strip()

        if value == "":
            return default

        return int(float(value))

    except:
        return default

def safe_price(value, default=0):
    """
    khusus price karena biasanya:
    - "Rp 12.000"
    - "12000"
    - "12K"
    """

    try:
        if value is None:
            return default

        value = str(value).lower().replace("rp", "").replace(" ", "").strip()

        if value == "":
            return default

        if "k" in value:
            return int(float(value.replace("k", "")) * 1000)

        return int(float(value.replace(".", "").replace(",", "")))

    except:
        return default


def mapping_untuk_llm(hasil):
    hasil_formatted = []

    for product in hasil:
        # 1. Ambil analysis_json jika ada, kalau tidak ada beri dict kosong {}
        analysis_data = product.get("product_analysis", {}) or {}
        analysis_json = analysis_data.get("analysis_json", {}) or {}
        
        # 2. Susun dict baru sesuai struktur yang kamu inginkan
        clean_product = {
            # Menggunakan tiktok_id_product sebagai string untuk product_id
            "product_id": str(product.get("tiktok_id_product")), 
            "title": product.get("title"),
            
            # Diambil dari dalam product_analysis -> analysis_json
            "opportunity_score": analysis_json.get("opportunity_score"),
            "rating": analysis_json.get("rating"),
            
            # Diambil dari level utama produk
            "sold": product.get("sold"),
            "commission": product.get("komisi"), # mapping komisi -> commission
            "price": product.get("price"),
            "creator_count": product.get("jumlah_kreator"), # mapping jumlah_kreator -> creator_count
            "ctr": product.get("ctr"),
            "positive_review": product.get("ulasan_positif"), # mapping ulasan_positif -> positive_review
            "stock": product.get("stok_tersedia"), # mapping stok_tersedia -> stock
            
            # Diambil dari status tren di dalam analysis_json
            "trend": analysis_json.get("scores", {}).get("trend", {}).get("status")
        }
        
        # Masukkan ke dalam list hasil
        hasil_formatted.append(clean_product)

    # --- UNTUK PRINT HASILNYA AGAR RAPI ---
    return hasil_formatted

def save_workflow(schedule_path, status="success"):

    schedule_file = os.path.join(
        schedule_path,
        "schedule.json"
    )

    try:

        with open(
            schedule_file,
            "r",
            encoding="utf-8"
        ) as file:
            schedule = json.load(file)


        schedule["schedule"]["status"] = status


        with open(
            schedule_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                schedule,
                file,
                indent=4,
                ensure_ascii=False
            )


        print(
            f"Schedule updated: {schedule_file}"
        )

        return True


    except Exception as e:

        print(
            f"Gagal save workflow: {e}"
        )

        return False

