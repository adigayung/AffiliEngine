"""
Database operations untuk Shopee Affiliate Product.

Tabel yang digunakan:
    shopee_products        : data produk Shopee (url_link = affiliate URL asli)
    tiktok_shopee_products : relasi TikTok Product <-> Shopee Product

Relasi bisnis:
    1 TikTok Product (tiktok_products.tiktok_id_product)
        |-- Shopee Product 1 (shopee_products.product_id)
        |-- Shopee Product 2
        `-- Shopee Product N
"""

from includes.mysql import get_connection


def get_shopee_product_by_url(url_link):
    """
    Cari Shopee Product berdasarkan affiliate URL (url_link).

    Jika sudah ada, JANGAN scrape ulang / insert ulang.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM shopee_products WHERE url_link = %s LIMIT 1",
                (url_link,)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def get_shopee_product_by_product_id(product_id):
    """Cari Shopee Product berdasarkan Shopee product_id."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM shopee_products WHERE product_id = %s LIMIT 1",
                (product_id,)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def get_relation(tiktok_product_id, shopee_product_id):
    """Cek apakah relasi TikTok Product <-> Shopee Product sudah ada."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tiktok_shopee_products
                WHERE tiktok_product_id = %s
                  AND shopee_product_id = %s
                LIMIT 1
                """,
                (tiktok_product_id, shopee_product_id)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def insert_relation(tiktok_product_id, shopee_product_id):
    """
    Insert relasi tiktok_shopee_products.
    INSERT IGNORE agar tidak membuat relasi duplikat.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT IGNORE INTO tiktok_shopee_products
                (tiktok_product_id, shopee_product_id)
                VALUES (%s, %s)
                """,
                (tiktok_product_id, shopee_product_id)
            )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def insert_shopee_product_and_relation(tiktok_product_id, data):
    """
    INSERT shopee_products + tiktok_shopee_products dalam SATU transaksi.

    Jika salah satu operasi gagal, seluruh operasi di-rollback sehingga
    tidak ada data setengah jadi.

    Args:
        tiktok_product_id: tiktok_id_product (VARCHAR)
        data: dict dengan keys product_id, shop_id, url_link, title,
              description, price, commission_rate, sold_count, rating,
              review_count, status
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO shopee_products
                (
                    product_id,
                    shop_id,
                    url_link,
                    title,
                    description,
                    price,
                    commission_rate,
                    sold_count,
                    rating,
                    review_count,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data["product_id"],
                    data.get("shop_id"),
                    data["url_link"],
                    data.get("title", ""),
                    data.get("description", ""),
                    data.get("price"),
                    data.get("commission_rate"),
                    data.get("sold_count"),
                    data.get("rating"),
                    data.get("review_count"),
                    data.get("status", "active"),
                )
            )

            cursor.execute(
                """
                INSERT IGNORE INTO tiktok_shopee_products
                (tiktok_product_id, shopee_product_id)
                VALUES (%s, %s)
                """,
                (tiktok_product_id, data["product_id"])
            )

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_shopee_products_for_tiktok(tiktok_product_id):
    """Semua Shopee Product yang terhubung ke satu TikTok Product."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT sp.*
                FROM shopee_products sp
                INNER JOIN tiktok_shopee_products tsp
                    ON tsp.shopee_product_id = sp.product_id
                WHERE tsp.tiktok_product_id = %s
                ORDER BY sp.created_at DESC
                """,
                (tiktok_product_id,)
            )
            return cursor.fetchall()
    finally:
        conn.close()


def remove_shopee_product_relation(tiktok_product_id, shopee_product_id):
    """
    Hapus relasi tiktok_shopee_products.

    Jika tidak ada relasi lain yang memakai Shopee Product tersebut,
    hapus juga baris shopee_products-nya. Semua dalam satu transaksi.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM tiktok_shopee_products
                WHERE tiktok_product_id = %s
                  AND shopee_product_id = %s
                """,
                (tiktok_product_id, shopee_product_id)
            )

            cursor.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM tiktok_shopee_products
                WHERE shopee_product_id = %s
                """,
                (shopee_product_id,)
            )
            remaining = cursor.fetchone()["cnt"]

            if remaining == 0:
                cursor.execute(
                    "DELETE FROM shopee_products WHERE product_id = %s",
                    (shopee_product_id,)
                )

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
