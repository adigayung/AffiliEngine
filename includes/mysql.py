# File : includes\mysql.py
import pymysql
import json
import datetime
from includes.config_loader import get_db_config

# =========================
# MYSQL CONFIG
# =========================
config = get_db_config()

MYSQL_HOST = config["mysql"]["host"]
MYSQL_USER = config["mysql"]["user"]
MYSQL_PASSWORD = config["mysql"]["password"]
MYSQL_DATABASE = config["mysql"]["database"]

# =========================
# CONNECTION
# =========================

def get_connection():

    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )

def get_product_analysis(product_id: int):

    # cara pakainya : 
    # analysis = get_product_analysis(product_id)
    # print(analysis["analysis_json"]["opportunity_score"])

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            sql = """
                SELECT *
                FROM tiktok_product_analysis
                WHERE product_id=%s
                ORDER BY id DESC
                LIMIT 1
            """

            cursor.execute(sql, (product_id,))

            row = cursor.fetchone()

            if row and row["analysis_json"]:

                if isinstance(row["analysis_json"], str):
                    row["analysis_json"] = json.loads(row["analysis_json"])

            return row

    finally:
        conn.close()

def save_product_analysis(
    product_id: int,
    analysis: dict,
    engine_version: str = "v1"
) -> int:

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT id FROM tiktok_product_analysis WHERE product_id=%s LIMIT 1",
                (product_id,)
            )

            row = cursor.fetchone()

            if row:

                cursor.execute("""
                    UPDATE tiktok_product_analysis
                    SET
                        engine_version=%s,
                        analysis_json=%s
                    WHERE id=%s
                """, (
                    engine_version,
                    json.dumps(analysis, ensure_ascii=False),
                    row["id"]
                ))

                analysis_id = row["id"]

            else:

                cursor.execute("""
                    INSERT INTO tiktok_product_analysis
                    (
                        product_id,
                        engine_version,
                        analysis_json
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s
                    )
                """, (
                    product_id,
                    engine_version,
                    json.dumps(analysis, ensure_ascii=False)
                ))

                analysis_id = cursor.lastrowid

        conn.commit()

        return analysis_id

    finally:
        conn.close()


def get_llm_analysis(product_id: int):

    # cara pakainya :
    # llm = get_llm_analysis(product_id)

    # if llm:

    #     print(llm["id"])
    #     print(llm["provider"])
    #     print(llm["model"])
    #     print(llm["llm_analysis"])


    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            sql = """
                SELECT *
                FROM tiktok_product_llm_analysis
                WHERE product_id=%s
                ORDER BY id DESC
                LIMIT 1
            """

            cursor.execute(sql, (product_id,))

            return cursor.fetchone()

    finally:
        conn.close()


def save_llm_analysis(
    product_id: int,
    analysis_id: int,
    provider: str,
    model: str,
    llm_analysis: str,
    prompt_version: str = "v1"
) -> int:

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT id FROM tiktok_product_llm_analysis WHERE product_id=%s LIMIT 1",
                (product_id,)
            )

            row = cursor.fetchone()

            if row:

                cursor.execute("""
                    UPDATE tiktok_product_llm_analysis
                    SET
                        analysis_id=%s,
                        provider=%s,
                        model=%s,
                        prompt_version=%s,
                        llm_analysis=%s
                    WHERE id=%s
                """, (
                    analysis_id,
                    provider,
                    model,
                    prompt_version,
                    llm_analysis,
                    row["id"]
                ))

                llm_analysis_id = row["id"]

            else:

                cursor.execute("""
                    INSERT INTO tiktok_product_llm_analysis
                    (
                        product_id,
                        analysis_id,
                        provider,
                        model,
                        prompt_version,
                        llm_analysis
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                """, (
                    product_id,
                    analysis_id,
                    provider,
                    model,
                    prompt_version,
                    llm_analysis
                ))

                llm_analysis_id = cursor.lastrowid

        conn.commit()

        return llm_analysis_id

    finally:
        conn.close()
# =========================
# GET TIKTOK ID PRODUCT FROM LOCAL ID
# =========================

def get_tiktok_id_product(product_id: int):
    """Mendapatkan tiktok_id_product dari primary key id tiktok_products.
    
    Args:
        product_id: id primary key dari tiktok_products (bukan tiktok_id_product)
    
    Returns:
        str: tiktok_id_product atau None jika tidak ditemukan
    """
    connection = get_connection()
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT tiktok_id_product
                FROM tiktok_products
                WHERE id = %s
                LIMIT 1
            """
            cursor.execute(sql, (product_id,))
            result = cursor.fetchone()
            if result:
                return result["tiktok_id_product"]
            return None
    except Exception as e:
        print(f"get_tiktok_id_product() error: {e}")
        return None
    finally:
        connection.close()

# =========================
# SAVE PRODUCT
# =========================


def save_product(data):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT id FROM tiktok_products WHERE tiktok_id_product=%s LIMIT 1",
                (data.get("tiktok_id_product", ""),)
            )

            row = cursor.fetchone()

            if row:

                cursor.execute("""
                    UPDATE tiktok_products SET
                        title=%s,
                        description=%s,
                        price=%s,
                        rating=%s,
                        vote=%s,
                        sold=%s,
                        product_link=%s,
                        komisi=%s,
                        stok_tersedia=%s,
                        ulasan_positif=%s,
                        pesanan=%s,
                        ctr=%s,
                        jumlah_kreator=%s,
                        pembeli_keranjang=%s
                    WHERE id=%s
                """, (
                    data.get("title", ""),
                    data.get("description", ""),
                    data.get("price", 0),
                    data.get("rating", 0),
                    data.get("vote", 0),
                    data.get("sold", 0),
                    data.get("product_link", ""),
                    data.get("komisi", 0),
                    data.get("stok_tersedia", 0),
                    data.get("ulasan_positif", 0),
                    data.get("pesanan", 0),
                    data.get("ctr", 0),
                    data.get("jumlah_kreator", 0),
                    data.get("pembeli_keranjang", 0),
                    row["id"]
                ))

                product_id = row["id"]

            else:

                cursor.execute("""
                    INSERT INTO tiktok_products (
                        tiktok_id_product,
                        title,
                        description,
                        price,
                        rating,
                        vote,
                        sold,
                        product_link,
                        komisi,
                        stok_tersedia,
                        ulasan_positif,
                        pesanan,
                        ctr,
                        jumlah_kreator,
                        pembeli_keranjang
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    data.get("tiktok_id_product", ""),
                    data.get("title", ""),
                    data.get("description", ""),
                    data.get("price", 0),
                    data.get("rating", 0),
                    data.get("vote", 0),
                    data.get("sold", 0),
                    data.get("product_link", ""),
                    data.get("komisi", 0),
                    data.get("stok_tersedia", 0),
                    data.get("ulasan_positif", 0),
                    data.get("pesanan", 0),
                    data.get("ctr", 0),
                    data.get("jumlah_kreator", 0),
                    data.get("pembeli_keranjang", 0),
                ))

                product_id = cursor.lastrowid

        connection.commit()

        return product_id

    finally:
        connection.close()


# =========================
# PRODUCTS
# =========================

def remove_product(product_id: int):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            sql = """
                DELETE
                FROM tiktok_products
                WHERE id = %s
                LIMIT 1
            """

            cursor.execute(sql, (product_id,))

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()

def get_product(product_id: int):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            sql = """
                SELECT *
                FROM tiktok_products
                WHERE tiktok_id_product = %s
                LIMIT 1
            """

            cursor.execute(sql, (product_id,))
            result = cursor.fetchone()

            if not result:
                return None

            result["product_analysis"] = get_product_analysis(
                result["id"]
            )

            result["llm_analysis"] = get_llm_analysis(
                result["id"]
            )

        return result

    finally:
        connection.close()

def get_product_basic(product_id: int):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            sql = """
                SELECT *
                FROM tiktok_products
                WHERE tiktok_id_product = %s
                LIMIT 1
            """

            cursor.execute(sql, (product_id,))
            result = cursor.fetchone()

            if not result:
                return None

        return result

    finally:
        connection.close()


# =========================
# GET ALL PRODUCTS
# =========================
def get_all_products():

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            sql = """
                SELECT *
                FROM tiktok_products
                ORDER BY id DESC
            """

            cursor.execute(sql)
            result = cursor.fetchall()

        return result

    finally:
        connection.close()

# =========================
# Creator MYSQL
# =========================
def add_creator(data):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            sql = """
                INSERT INTO creators
                (
                    username,
                    display_name,
                    profile_image,
                    is_active
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    1
                )
            """

            cursor.execute(sql, (

                data["username"],
                data["display_name"],
                data["profile_image"]

            ))

            connection.commit()

            return cursor.lastrowid

    finally:

        connection.close()

def remove_creator(creator_id):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            sql = """
                DELETE FROM creators
                WHERE id=%s
                LIMIT 1
            """

            cursor.execute(sql, (creator_id,))

            connection.commit()

            return cursor.rowcount

    finally:

        connection.close()

def edit_creator(creator_id, data):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            sql = """
                UPDATE creators
                SET
                    username=%s,
                    display_name=%s,
                    profile_image=%s,
                    is_active=%s
                WHERE id=%s
            """

            cursor.execute(sql, (

                data["username"],
                data["display_name"],
                data["profile_image"],
                data["is_active"],
                creator_id

            ))

            connection.commit()

            return cursor.rowcount

    finally:

        connection.close()

def get_creator(creator_id):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            sql = """
                SELECT *
                FROM creators
                WHERE id=%s
                LIMIT 1
            """

            cursor.execute(sql, (creator_id,))

            return cursor.fetchone()

    finally:

        connection.close()

def get_creator_list():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            sql = """
                SELECT *
                FROM creators
                ORDER BY id DESC
            """

            cursor.execute(sql)

            return cursor.fetchall()

    finally:

        connection.close()

# =========================
# SAVE UPLOAD JOB
# =========================

def save_upload_job(
    creator_id,
    batch_id,
    product_id,
    schedule_datetime,
    folder,
    status="pending"
):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            sql = """
                INSERT INTO upload_jobs
                (
                    creator_id,
                    batch_id,
                    product_id,
                    schedule_datetime,
                    folder,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON DUPLICATE KEY UPDATE

                    product_id = VALUES(product_id),

                    folder = VALUES(folder),

                    status = VALUES(status),

                    updated_at = CURRENT_TIMESTAMP
            """

            cursor.execute(
                sql,
                (
                    creator_id,
                    batch_id,
                    product_id,
                    schedule_datetime,
                    folder,
                    status
                )
            )

        conn.commit()

        return cursor.lastrowid

    except Exception as e:

        conn.rollback()

        print(e)

        return None

    finally:

        conn.close()

# =========================
# SAVE SCHEDULE BATCH
# =========================

def save_schedule_batch(
    creator_id,
    upload_directory,
    start_datetime,
    finish_datetime,
    interval_hour,
    total_jobs,
    status="active"
):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            # =========================
            # CHECK EXISTING BATCH
            # =========================

            cursor.execute(
                """
                SELECT id
                FROM schedule_batches
                WHERE creator_id=%s
                AND upload_directory=%s
                AND start_datetime=%s
                AND finish_datetime=%s
                LIMIT 1
                """,
                (
                    creator_id,
                    upload_directory,
                    start_datetime,
                    finish_datetime
                )
            )

            row = cursor.fetchone()

            # =========================
            # UPDATE
            # =========================

            if row:

                cursor.execute(
                    """
                    UPDATE schedule_batches
                    SET
                        interval_hour=%s,
                        total_jobs=%s,
                        status=%s
                    WHERE id=%s
                    """,
                    (
                        interval_hour,
                        total_jobs,
                        status,
                        row["id"]
                    )
                )

                conn.commit()

                return row["id"]

            # =========================
            # INSERT
            # =========================

            cursor.execute(
                """
                INSERT INTO schedule_batches
                (
                    creator_id,
                    upload_directory,
                    start_datetime,
                    finish_datetime,
                    interval_hour,
                    total_jobs,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    creator_id,
                    upload_directory,
                    start_datetime,
                    finish_datetime,
                    interval_hour,
                    total_jobs,
                    status
                )
            )

            batch_id = cursor.lastrowid

        conn.commit()

        return batch_id

    except Exception as e:

        conn.rollback()

        print(f"save_schedule_batch() : {e}")

        return None

    finally:

        conn.close()

# =========================
# UPDATE UPLOAD JOB
# =========================

# =========================
# UPDATE UPLOAD JOB
# =========================

def update_upload_job(
    job_id,
    status
):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            if status == "uploaded":

                cursor.execute(
                    """
                    UPDATE upload_jobs
                    SET
                        status=%s,
                        uploaded_at=CURRENT_TIMESTAMP,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,
                    (
                        status,
                        job_id
                    )
                )

            else:

                cursor.execute(
                    """
                    UPDATE upload_jobs
                    SET
                        status=%s,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,
                    (
                        status,
                        job_id
                    )
                )

        conn.commit()

        return True

    except Exception as e:

        conn.rollback()

        print(f"update_upload_job() : {e}")

        return False

    finally:

        conn.close()

# =========================
# CHECK AND UPDATE BATCH STATUS
# =========================

def check_and_update_batch_status(batch_id):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            # Ambil semua upload_job dalam batch ini
            cursor.execute(
                """
                SELECT id, status
                FROM upload_jobs
                WHERE batch_id=%s
                """,
                (batch_id,)
            )

            jobs = cursor.fetchall()

            if not jobs:
                return False

            # Periksa apakah semua status == "uploaded"
            all_uploaded = all(
                job["status"] == "uploaded" for job in jobs
            )

            if all_uploaded:

                cursor.execute(
                    """
                    UPDATE schedule_batches
                    SET status=%s
                    WHERE id=%s
                    """,
                    ("completed", batch_id)
                )

                conn.commit()

                print(
                    f"check_and_update_batch_status() : "
                    f"Batch {batch_id} marked as completed"
                )

                return True

            else:

                print(
                    f"check_and_update_batch_status() : "
                    f"Batch {batch_id} masih ada job yang belum uploaded"
                )

                return False

    except Exception as e:

        conn.rollback()

        print(f"check_and_update_batch_status() : {e}")

        return False

    finally:

        conn.close()








# =============================================================================
# VIDEO PERFORMANCE FUNCTIONS - Arsitektur Baru
# =============================================================================
# Source of Truth: Akun TikTok
# 1. Data Video TikTok (tiktok_videos) - data relatif tetap
# 2. Statistik Harian (tiktok_video_stats) - data yang berubah setiap hari
# 3. Matching ke upload_jobs sebagai relasi opsional
# =============================================================================


def upsert_tiktok_video(creator_id, video_data):
    """
    Insert atau update METADATA video TikTok ke tabel tiktok_videos.

    Hanya menyimpan metadata video:
    - video_id, creator_id, video_url, caption, upload_time
    - first_detected, last_scan
    - duration (hanya diisi sekali)

    Statistik (views, likes, comments, shares) disimpan TERPISAH
    ke tiktok_video_stats melalui upsert_video_daily_stats().

    Returns:
        int: Primary key (id) dari tiktok_videos
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, duration FROM tiktok_videos WHERE video_id = %s AND creator_id = %s LIMIT 1",
                (video_data["video_id"], creator_id)
            )
            row = cursor.fetchone()
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if row:
                video_pk = row["id"]
                existing_duration = row["duration"]

                # UPDATE metadata (caption bisa berubah, last_scan selalu)
                # Duration hanya di-update jika masih NULL atau 0
                cursor.execute("""
                    UPDATE tiktok_videos SET
                        caption = %s,
                        last_scan = %s,
                        duration = IFNULL(duration, %s)
                    WHERE id = %s
                """, (
                    video_data.get("caption", ""),
                    now_str,
                    video_data.get("duration") or None,
                    video_pk
                ))
                conn.commit()
                return video_pk
            else:
                # INSERT metadata video baru
                cursor.execute("""
                    INSERT INTO tiktok_videos
                    (video_id, creator_id, video_url, caption,
                     upload_time, first_detected, last_scan, duration)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    video_data["video_id"],
                    creator_id,
                    video_data.get("video_url", video_data.get("url", "")),
                    video_data.get("caption", ""),
                    video_data.get("upload_time"),
                    now_str,
                    now_str,
                    video_data.get("duration") or None,
                ))
                video_pk = cursor.lastrowid
                conn.commit()
                return video_pk
    except Exception as e:
        conn.rollback()
        print(f"upsert_tiktok_video() error: {e}")
        raise
    finally:
        conn.close()


def upsert_video_daily_stats(video_pk, views, likes=0, comments=0, shares=0, favorites=0, snapshot_time=None):
    """
    Simpan statistik harian video.
    Satu video hanya memiliki satu record per tanggal (via snapshot_time).

    - Jika tanggal hari ini belum ada → INSERT row baru.
    - Jika tanggal hari ini sudah ada → UPDATE row yang sama (snapshot_time
      diperbarui, views/likes/comments/shares/favorites di-overwrite).

    Dengan demikian dalam satu hari hanya ada SATU snapshot per video.

    Returns:
        bool: True jika berhasil
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if snapshot_time is None:
                snapshot_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(snapshot_time, datetime.datetime):
                snapshot_time = snapshot_time.strftime("%Y-%m-%d %H:%M:%S")

            # Cari apakah sudah ada record untuk tanggal ini
            today_date = snapshot_time[:10]  # YYYY-MM-DD
            cursor.execute("""
                SELECT id FROM tiktok_video_stats
                WHERE video_id = %s AND DATE(snapshot_time) = %s
                LIMIT 1
            """, (video_pk, today_date))
            row = cursor.fetchone()

            if row:
                # UPDATE row yang sama — perbarui snapshot_time dan semua stat
                cursor.execute("""
                    UPDATE tiktok_video_stats SET
                        snapshot_time = %s,
                        views = %s,
                        likes = %s,
                        comments = %s,
                        shares = %s,
                        favorites = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (snapshot_time, views, likes, comments, shares, favorites, row["id"]))
            else:
                # INSERT row baru
                cursor.execute("""
                    INSERT INTO tiktok_video_stats
                    (video_id, snapshot_time, views, likes, comments, shares, favorites)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (video_pk, snapshot_time, views, likes, comments, shares, favorites))

            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"upsert_video_daily_stats() error: {e}")
        return False
    finally:
        conn.close()


def match_video_to_upload_job(creator_id, video_id_tiktok):
    """
    Coba match-kan satu video TikTok ke upload_jobs.

    Kriteria matching:
    - creator_id sama
    - upload_job.status = 'uploaded'
    - upload_job.schedule_datetime <= NOW()
    - upload_job.video_id IS NULL (belum ter-match)

    Jika ditemukan, update relasi dua arah.

    Returns:
        dict atau None: {upload_job_id, match_score} jika match, None jika tidak
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Cari upload_job yang cocok
            cursor.execute("""
                SELECT uj.id
                FROM upload_jobs uj
                WHERE uj.creator_id = %s
                  AND uj.status = 'uploaded'
                  AND uj.schedule_datetime <= %s
                  AND uj.video_id IS NULL
                ORDER BY ABS(TIMESTAMPDIFF(SECOND, uj.schedule_datetime, %s)) ASC
                LIMIT 1
            """, (creator_id, now_str, now_str))

            job = cursor.fetchone()
            if not job:
                return None

            upload_job_id = job["id"]
            match_score = 1.0  # Exact match by time proximity

            # Update tiktok_videos
            cursor.execute("""
                UPDATE tiktok_videos
                SET upload_job_id = %s, match_score = %s, match_method = 'auto',
                    matched_at = CURRENT_TIMESTAMP
                WHERE video_id = %s AND creator_id = %s
            """, (upload_job_id, match_score, video_id_tiktok, creator_id))

            # Update upload_jobs
            cursor.execute("""
                UPDATE upload_jobs SET video_id = %s WHERE id = %s
            """, (video_id_tiktok, upload_job_id))

            conn.commit()

            return {
                "upload_job_id": upload_job_id,
                "match_score": match_score,
            }
    except Exception as e:
        conn.rollback()
        print(f"match_video_to_upload_job() error: {e}")
        return None
    finally:
        conn.close()


def get_video_performance_summary(creator_id):
    """
    Summary statistik Video Performance untuk satu creator.

    Total views/likes dihitung dari tiktok_video_stats (data scan terbaru per video),
    karena tiktok_videos tidak menyimpan kolom statistik.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Last scan
            cursor.execute(
                "SELECT MAX(last_scan) AS last_scan FROM tiktok_videos WHERE creator_id = %s",
                (creator_id,)
            )
            row = cursor.fetchone()
            last_scan = row["last_scan"] if row else None

            # Total videos
            cursor.execute(
                "SELECT COUNT(*) AS total FROM tiktok_videos WHERE creator_id = %s",
                (creator_id,)
            )
            total_videos = cursor.fetchone()["total"] or 0

                        # Total views & likes dari tiktok_video_stats (data scan terbaru per video)
            cursor.execute("""
                SELECT
                    COALESCE(SUM(s.views), 0) AS total_views,
                    COALESCE(SUM(s.likes), 0) AS total_likes
                FROM tiktok_video_stats s
                INNER JOIN (
                    SELECT video_id, MAX(DATE(snapshot_time)) AS max_date
                    FROM tiktok_video_stats
                    WHERE video_id IN (
                        SELECT id FROM tiktok_videos WHERE creator_id = %s
                    )
                    GROUP BY video_id
                ) latest ON s.video_id = latest.video_id AND DATE(s.snapshot_time) = latest.max_date
            """, (creator_id,))
            stats_row = cursor.fetchone()
            total_views = stats_row["total_views"] if stats_row else 0
            total_likes = stats_row["total_likes"] if stats_row else 0

            # Matched count (untuk info saja)
            cursor.execute("""
                SELECT COUNT(*) AS total FROM tiktok_videos
                WHERE creator_id = %s AND upload_job_id IS NOT NULL
            """, (creator_id,))
            matched = cursor.fetchone()["total"] or 0

            return {
                "last_scan": last_scan.strftime("%Y-%m-%d %H:%M") if last_scan else None,
                "total_videos": total_videos,
                "total_views": total_views,
                "total_likes": total_likes,
                "matched": matched,
            }
    except Exception as e:
        print(f"get_video_performance_summary() error: {e}")
        return {
            "last_scan": None, "total_videos": 0, "total_views": 0,
            "total_likes": 0, "matched": 0,
        }
    finally:
        conn.close()


def get_video_performance_list(creator_id):
    """
    Ambil daftar video TikTok untuk halaman Video Performance.

    Data views/likes/comments/shares diambil dari tiktok_video_stats
    (scan terbaru), karena tiktok_videos tidak menyimpan kolom statistik.

    Growth dihitung dari selisih dengan scan hari sebelumnya.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    v.id,
                    v.video_id,
                    v.video_url,
                    v.caption,
                    v.upload_time,
                    v.last_scan,
                    v.upload_job_id,
                                        -- Data statistik terkini (scan terbaru)
                    curr.views AS current_views,
                    curr.likes AS current_likes,
                    curr.comments AS current_comments,
                    curr.shares AS current_shares,
                    -- Data statistik kemarin (untuk growth)
                    prev.views AS prev_views,
                    prev.likes AS prev_likes,
                    prev.comments AS prev_comments,
                    prev.shares AS prev_shares
                FROM tiktok_videos v
                LEFT JOIN tiktok_video_stats curr
                    ON curr.video_id = v.id
                    AND DATE(curr.snapshot_time) = (
                        SELECT MAX(DATE(snapshot_time)) FROM tiktok_video_stats
                        WHERE video_id = v.id
                    )
                LEFT JOIN tiktok_video_stats prev
                    ON prev.video_id = v.id
                    AND DATE(prev.snapshot_time) = CURDATE() - INTERVAL 1 DAY
                WHERE v.creator_id = %s
                ORDER BY v.upload_time DESC
            """, (creator_id,))
            rows = cursor.fetchall()

            result = []
            for row in rows:
                current_views = row["current_views"] or 0
                prev_views = row["prev_views"] or 0
                views_growth = current_views - prev_views if prev_views > 0 else None

                current_likes = row["current_likes"] or 0
                prev_likes = row["prev_likes"] or 0
                likes_growth = current_likes - prev_likes if prev_likes > 0 else None

                current_comments = row["current_comments"] or 0
                prev_comments = row["prev_comments"] or 0
                comments_growth = current_comments - prev_comments if prev_comments > 0 else None

                current_shares = row["current_shares"] or 0
                prev_shares = row["prev_shares"] or 0
                shares_growth = current_shares - prev_shares if prev_shares > 0 else None

                result.append({
                    "id": row["id"],
                    "video_id": row["video_id"],
                    "video_url": row["video_url"],
                    "caption": row["caption"],
                    "upload_time": row["upload_time"],
                    "last_scan": row["last_scan"],
                    "views": current_views,
                    "views_growth": views_growth,
                    "likes": current_likes,
                    "likes_growth": likes_growth,
                    "comments": current_comments,
                    "comments_growth": comments_growth,
                    "shares": current_shares,
                    "shares_growth": shares_growth,
                    "upload_job_id": row["upload_job_id"],
                })
            return result
    except Exception as e:
        print(f"get_video_performance_list() error: {e}")
        return []
    finally:
        conn.close()


# =============================================================================
# BACKWARD COMPATIBILITY - Fungsi lama (masih dipanggil oleh matching engine)
# =============================================================================

def insert_or_update_video(creator_id, video_data):
    """Backward compatibility - panggil upsert_tiktok_video"""
    return upsert_tiktok_video(creator_id, video_data)


def insert_video_stats(video_id, views, snapshot_time=None):
    """Backward compatibility - panggil upsert_video_daily_stats dengan format lama"""
    if snapshot_time is None:
        snap = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        if isinstance(snapshot_time, str):
            snap = snapshot_time
        else:
            snap = snapshot_time.strftime("%Y-%m-%d %H:%M:%S")
    return upsert_video_daily_stats(video_id, views, snapshot_time=snap)


def get_unmatched_videos_for_matching(creator_id):
    """Backward compatibility - ambil video tanpa upload_job_id"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT video_id, upload_time, caption
                FROM tiktok_videos
                WHERE creator_id = %s AND upload_job_id IS NULL
                ORDER BY upload_time DESC
            """, (creator_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"get_unmatched_videos_for_matching() error: {e}")
        return []
    finally:
        conn.close()


def get_upload_jobs_for_matching(creator_id):
    """Backward compatibility"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, product_id, schedule_datetime, folder
                FROM upload_jobs
                WHERE creator_id = %s AND video_id IS NULL
                AND status IN ('pending', 'uploaded')
                ORDER BY schedule_datetime DESC
            """, (creator_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"get_upload_jobs_for_matching() error: {e}")
        return []
    finally:
        conn.close()


def update_video_matching(video_id, upload_job_id, match_score, match_method='auto'):
    """Backward compatibility"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tiktok_videos
                SET upload_job_id = %s, match_score = %s, match_method = %s,
                    matched_at = CURRENT_TIMESTAMP
                WHERE video_id = %s
            """, (upload_job_id, match_score, match_method, video_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"update_video_matching() error: {e}")
        return False
    finally:
        conn.close()


def update_upload_job_video_id(job_id, video_id):
    """Backward compatibility"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE upload_jobs SET video_id = %s WHERE id = %s", (video_id, job_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"update_upload_job_video_id() error: {e}")
        return False
    finally:
        conn.close()


def get_creator_username(creator_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT username FROM creators WHERE id = %s LIMIT 1", (creator_id,))
            row = cursor.fetchone()
            return row["username"] if row else None
    except Exception as e:
        print(f"get_creator_username() error: {e}")
        return None
    finally:
        conn.close()


# =============================================================================
# VIDEO JOB MATCHER
# =============================================================================

MATCH_TOLERANCE_SECOND = 120


def match_tiktok_videos_to_jobs():
    """
    Match antara tiktok_videos (yang belum punya upload_job_id) dengan
    upload_jobs (status='uploaded', video_id IS NULL, schedule_datetime <= NOW()).

    Kriteria matching:
      - creator_id sama
      - selisih antara upload_time dan schedule_datetime <= 120 detik

    Update jika cocok:
      - tiktok_videos.upload_job_id = upload_jobs.id (hanya jika NULL)
      - upload_jobs.video_id = tiktok_videos.video_id (hanya jika NULL)

    Log:
      - [MATCH VIDEO] job=xxx video=xxx diff=xxs  (ketika match ditemukan)
      - [MATCH VIDEO] Tidak ada data  (ketika tidak ada match)

    Returns:
        int: Jumlah pasangan yang berhasil di-match
    """
    conn = None
    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            sql = """
            SELECT
                tv.id AS video_row_id,
                tv.video_id,
                tv.creator_id,
                tv.upload_time,
                uj.id AS job_id,
                uj.schedule_datetime,
                ABS(
                    TIMESTAMPDIFF(
                        SECOND,
                        uj.schedule_datetime,
                        tv.upload_time
                    )
                ) AS diff_second

            FROM tiktok_videos tv

            JOIN upload_jobs uj
                ON tv.creator_id = uj.creator_id

            WHERE
                tv.upload_job_id IS NULL
                AND uj.video_id IS NULL
                AND uj.status = 'uploaded'
                AND uj.schedule_datetime <= NOW()

            HAVING diff_second <= %s

            ORDER BY diff_second ASC
            """

            cursor.execute(
                sql,
                (MATCH_TOLERANCE_SECOND,)
            )

            matches = cursor.fetchall()

            if not matches:
                print(
                    "[MATCH VIDEO] Tidak ada data"
                )
                return 0

            total = 0

            for row in matches:
                video_row_id = row["video_row_id"]
                video_id = row["video_id"]
                job_id = row["job_id"]

                # isi tiktok_videos (hanya jika upload_job_id masih NULL)
                cursor.execute(
                    """
                    UPDATE tiktok_videos
                    SET upload_job_id=%s
                    WHERE id=%s
                    AND upload_job_id IS NULL
                    """,
                    (job_id, video_row_id)
                )

                # isi upload_jobs (hanya jika video_id masih NULL)
                cursor.execute(
                    """
                    UPDATE upload_jobs
                    SET video_id=%s
                    WHERE id=%s
                    AND video_id IS NULL
                    """,
                    (video_id, job_id)
                )

                total += 1

                print(
                    f"[MATCH VIDEO] "
                    f"job={job_id} "
                    f"video={video_id} "
                    f"diff={row['diff_second']}s"
                )
            conn.commit()
            return total

    except Exception as e:
        if conn:
            conn.rollback()
        print("[MATCH VIDEO ERROR]", e)
        return 0

    finally:
        if conn:
            conn.close()


# =============================================================================
# BACKWARD COMPATIBILITY - Fungsi lama (masih dipanggil oleh matching engine)
# =============================================================================
