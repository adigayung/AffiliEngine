"""
Shopee Affiliate Product Service.

Mengkoordinasikan seluruh alur bisnis penambahan Shopee Affiliate Product
pada halaman /product/<tiktok_product_id>:

    1. Validasi TikTok Product
    2. Validasi Shopee Affiliate URL
    3. Cek `shopee_products.url_link` -> jika sudah ada, JANGAN scrape ulang
    4. Scrape metadata via existing driver (profile_path="./chromium")
    5. INSERT shopee_products + tiktok_shopee_products (satu transaksi)

PENTING:
    - url_link selalu berisi affiliate URL ASLI dari user (bukan URL redirect).
    - Affiliate URL akan digunakan kembali oleh Facebook Affiliate Automation.
"""

import logging

from selenium.common.exceptions import TimeoutException

from includes.mysql import get_product_basic
from includes.product.shopee import db
from includes.product.shopee import scraper
from includes.product.shopee.validator import is_valid_affiliate_url

logger = logging.getLogger(__name__)

# ==============================
# PESAN ERROR (untuk user)
# ==============================
ERROR_URL_EMPTY = "Please enter a Shopee affiliate URL."
ERROR_URL_INVALID = (
    "Invalid Shopee affiliate link. Please use a link in the format "
    "https://s.shopee.co.id/..."
)
ERROR_METADATA = "Unable to retrieve Shopee product information."
ERROR_ALREADY_LINKED = (
    "This Shopee product is already linked to this TikTok product."
)
ERROR_TIMEOUT = (
    "Unable to retrieve Shopee product information. Please try again."
)
ERROR_PRODUCT_NOT_FOUND = "TikTok product not found."

MSG_LINKED = "Shopee product linked successfully."
MSG_ADDED = "Shopee product added successfully."


def add_shopee_product(tiktok_product_id, raw_url):
    """
    Full flow penambahan Shopee Affiliate Product.

    Returns:
        dict: {"success": bool, "message": str}
    """
    # ==============================
    # 1. VALIDASI TIKTOK PRODUCT
    # ==============================
    product = get_product_basic(tiktok_product_id)
    if not product:
        return {"success": False, "message": ERROR_PRODUCT_NOT_FOUND}

    # ==============================
    # 2. VALIDASI SHOPEE AFFILIATE URL
    # ==============================
    if not raw_url or not str(raw_url).strip():
        return {"success": False, "message": ERROR_URL_EMPTY}

    affiliate_url = str(raw_url).strip()

    if not is_valid_affiliate_url(affiliate_url):
        return {"success": False, "message": ERROR_URL_INVALID}

    # ==============================
    # 3. CEK URL_LINK DI SHOPEE_PRODUCTS
    #    (JANGAN scrape ulang jika sudah ada)
    # ==============================
    existing = db.get_shopee_product_by_url(affiliate_url)

    if existing:
        # Relasi sudah ada -> jangan buat duplicate relation
        if db.get_relation(tiktok_product_id, existing["product_id"]):
            return {"success": True, "message": ERROR_ALREADY_LINKED}

        # Product sudah ada tapi relasi belum -> insert relasi saja
        db.insert_relation(tiktok_product_id, existing["product_id"])
        return {"success": True, "message": MSG_LINKED}

    # ==============================
    # 4. SCRAPE METADATA (existing driver)
    # ==============================
    try:
        metadata = scraper.fetch_shopee_metadata(affiliate_url)
    except TimeoutException:
        return {"success": False, "message": ERROR_TIMEOUT}
    except Exception:
        logger.exception("Shopee metadata fetch gagal")
        return {"success": False, "message": ERROR_METADATA}

    if not metadata or not metadata.get("product_id"):
        return {"success": False, "message": ERROR_METADATA}

    # ==============================
    # 4b. JIKA PRODUCT_ID SUDAH ADA (misal affiliate URL lain)
    #     -> gunakan existing, jangan insert ulang
    # ==============================
    existing_by_id = db.get_shopee_product_by_product_id(
        str(metadata["product_id"])
    )

    if existing_by_id:
        if db.get_relation(tiktok_product_id, existing_by_id["product_id"]):
            return {"success": True, "message": ERROR_ALREADY_LINKED}

        db.insert_relation(tiktok_product_id, existing_by_id["product_id"])
        return {"success": True, "message": MSG_LINKED}

    # ==============================
    # 5. INSERT SHOPEE_PRODUCTS + TIKTOK_SHOPEE_PRODUCTS (transaction)
    # ==============================
    data = {
        "product_id": str(metadata["product_id"])[:100],
        "shop_id": metadata.get("shop_id"),
        # url_link WAJIB affiliate URL asli (bukan URL redirect)
        "url_link": affiliate_url,
        "title": metadata.get("title") or "",
        "description": metadata.get("description") or "",
        "price": metadata.get("price"),
        "commission_rate": metadata.get("commission_rate"),
        "sold_count": metadata.get("sold_count"),
        "rating": metadata.get("rating"),
        "review_count": metadata.get("review_count"),
        "status": "active",
    }

    try:
        db.insert_shopee_product_and_relation(tiktok_product_id, data)
    except Exception:
        logger.exception("Insert shopee product gagal")
        return {"success": False, "message": ERROR_METADATA}

    return {"success": True, "message": MSG_ADDED}


def remove_shopee_product(tiktok_product_id, shopee_product_id):
    """
    Hapus relasi TikTok Product <-> Shopee Product.

    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        db.remove_shopee_product_relation(tiktok_product_id, shopee_product_id)
        return {"success": True}
    except Exception:
        logger.exception("Remove shopee product gagal")
        return {"success": False, "message": "Unable to remove Shopee product."}
