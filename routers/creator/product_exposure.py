from flask import Blueprint, render_template, request, abort
from includes.mysql import get_connection, get_creator
import datetime

creator_product_exposure_bp = Blueprint(
    "creator_product_exposure",
    __name__,
    url_prefix="/creator"
)


def get_product_exposure_data(creator_id: int, search_query: str = None):
    """
    Ambil data Product Exposure untuk satu Creator.

    Published  = status='uploaded' AND schedule_datetime <= NOW()
    Scheduled  = status='uploaded' AND schedule_datetime > NOW()
    Pending    = selain uploaded (tidak dihitung)

    Per produk:
      - published_count
      - scheduled_count
      - total = published + scheduled
      - percentage = published / total_published_creator * 100
      - first_published, last_published (hanya untuk yang benar-benar published)

    Returns:
        dict or None
    """
    creator = get_creator(creator_id)
    if not creator:
        return None

    now = datetime.datetime.now()
    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            # ==============================
            # TOTAL PUBLISHED CREATOR
            # ==============================
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM upload_jobs
                WHERE creator_id = %s
                  AND status = 'uploaded'
                  AND schedule_datetime <= %s
            """, (creator_id, now))
            total_published_creator = cursor.fetchone()["total"] or 0

            # ==============================
            # TOTAL SCHEDULED CREATOR
            # ==============================
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM upload_jobs
                WHERE creator_id = %s
                  AND status = 'uploaded'
                  AND schedule_datetime > %s
            """, (creator_id, now))
            total_scheduled_creator = cursor.fetchone()["total"] or 0

            # ==============================
            # CEK APAKAH ADA PRODUCT TITLE
            # ==============================
            cursor.execute("""
                SELECT COUNT(*) AS cnt
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'tiktok_products'
                  AND COLUMN_NAME = 'title'
            """)
            has_title = cursor.fetchone()["cnt"] > 0

            # ==============================
            # QUERY AGREGASI PER PRODUK
            # ==============================
            # Published: status='uploaded' AND schedule_datetime <= NOW()
            # Scheduled: status='uploaded' AND schedule_datetime > NOW()
            # Diurutkan berdasarkan published_count DESC, total DESC
            if has_title:
                sql = """
                    SELECT
                        uj.product_id,
                        tp.id AS product_db_id,
                        tp.title AS product_name,
                        tp.tiktok_id_product,
                        SUM(CASE
                            WHEN uj.status = 'uploaded' AND uj.schedule_datetime <= %s
                            THEN 1 ELSE 0
                        END) AS published_count,
                        SUM(CASE
                            WHEN uj.status = 'uploaded' AND uj.schedule_datetime > %s
                            THEN 1 ELSE 0
                        END) AS scheduled_count,
                        MIN(CASE
                            WHEN uj.status = 'uploaded' AND uj.schedule_datetime <= %s
                            THEN uj.schedule_datetime
                        END) AS first_published,
                        MAX(CASE
                            WHEN uj.status = 'uploaded' AND uj.schedule_datetime <= %s
                            THEN uj.schedule_datetime
                        END) AS last_published
                    FROM upload_jobs uj
                    LEFT JOIN tiktok_products tp
                        ON tp.tiktok_id_product = uj.product_id
                    WHERE uj.creator_id = %s
                    GROUP BY uj.product_id, tp.id, tp.title, tp.tiktok_id_product
                    HAVING published_count > 0 OR scheduled_count > 0
                    ORDER BY published_count DESC, scheduled_count DESC
                """
            else:
                sql = """
                    SELECT
                        uj.product_id,
                        NULL AS product_db_id,
                        NULL AS product_name,
                        NULL AS tiktok_id_product,
                        SUM(CASE
                            WHEN uj.status = 'uploaded' AND uj.schedule_datetime <= %s
                            THEN 1 ELSE 0
                        END) AS published_count,
                        SUM(CASE
                            WHEN uj.status = 'uploaded' AND uj.schedule_datetime > %s
                            THEN 1 ELSE 0
                        END) AS scheduled_count,
                        MIN(CASE
                            WHEN uj.status = 'uploaded' AND uj.schedule_datetime <= %s
                            THEN uj.schedule_datetime
                        END) AS first_published,
                        MAX(CASE
                            WHEN uj.status = 'uploaded' AND uj.schedule_datetime <= %s
                            THEN uj.schedule_datetime
                        END) AS last_published
                    FROM upload_jobs uj
                    WHERE uj.creator_id = %s
                    GROUP BY uj.product_id
                    HAVING published_count > 0 OR scheduled_count > 0
                    ORDER BY published_count DESC, scheduled_count DESC
                """

            cursor.execute(sql, (now, now, now, now, creator_id))
            rows = cursor.fetchall()

    finally:
        conn.close()

    # ==============================
    # FORMAT DATA
    # ==============================
    products = []
    for row in rows:
        product_id = row["product_id"]

        # Product name
        product_name = row.get("product_name") or row.get("title")
        if not product_name:
            product_name = f"Product #{product_id}"

        # Thumbnail
        tiktok_id = row.get("tiktok_id_product") or product_id
        thumbnail = f"/static/products/{tiktok_id}/product/1.jpg"

        # Published / Scheduled / Total
        published_count = row["published_count"] or 0
        scheduled_count = row["scheduled_count"] or 0
        total = published_count + scheduled_count

        # Percentage based on Published only
        percentage = 0.0
        if total_published_creator > 0:
            percentage = round((published_count / total_published_creator) * 100, 2)

        # Format dates (hanya untuk Published)
        first_published = row["first_published"]
        last_published = row["last_published"]

        # First Published
        if first_published is not None:
            if isinstance(first_published, (datetime.datetime, datetime.date)):
                first_published_formatted = first_published.strftime("%d %b %Y")
            elif isinstance(first_published, str):
                try:
                    dt = datetime.datetime.strptime(first_published, "%Y-%m-%d %H:%M:%S")
                    first_published_formatted = dt.strftime("%d %b %Y")
                except ValueError:
                    first_published_formatted = str(first_published)
            else:
                first_published_formatted = "-"
        else:
            first_published_formatted = "-"

        # Last Published
        if last_published is not None:
            if isinstance(last_published, (datetime.datetime, datetime.date)):
                last_published_formatted = last_published.strftime("%d %b %Y")
            elif isinstance(last_published, str):
                try:
                    dt = datetime.datetime.strptime(last_published, "%Y-%m-%d %H:%M:%S")
                    last_published_formatted = dt.strftime("%d %b %Y")
                except ValueError:
                    last_published_formatted = str(last_published)
            else:
                last_published_formatted = "-"
        else:
            last_published_formatted = "-"

        products.append({
            "product_id": product_id,
            "product_db_id": row.get("product_db_id"),
            "product_name": product_name,
            "thumbnail": thumbnail,
            "published_count": published_count,
            "scheduled_count": scheduled_count,
            "total": total,
            "percentage": percentage,
            "first_published_formatted": first_published_formatted,
            "last_published_formatted": last_published_formatted,
        })

    # ==============================
    # FILTER SEARCH
    # ==============================
    if search_query:
        search_lower = search_query.lower()
        products = [
            p for p in products
            if search_lower in p["product_name"].lower()
        ]

    # ==============================
    # HITUNG JUMLAH PRODUK UNIK
    # ==============================
    total_unique_products = len(products)

    return {
        "creator": creator,
        "total_published": total_published_creator,
        "total_scheduled": total_scheduled_creator,
        "total_unique_products": total_unique_products,
        "products": products,
    }


@creator_product_exposure_bp.route("/<int:creator_id>/product-exposure")
def product_exposure(creator_id):
    """
    Halaman Product Exposure untuk satu Creator.
    URL: /creator/<creator_id>/product-exposure
    """
    search_query = request.args.get("search", "").strip()

    data = get_product_exposure_data(creator_id, search_query)

    if data is None:
        abort(404, description="Creator tidak ditemukan")

    creator = data["creator"]

    return render_template(
        "creator/product_exposure.html",
        page_title=f"Product Exposure - {creator.get('display_name', creator.get('username', 'Unknown'))}",
        exposure_data=data,
        search_query=search_query,
    )
