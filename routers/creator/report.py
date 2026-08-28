import datetime
import os
import re
import shutil

from flask import Blueprint, render_template, abort, jsonify, request
from includes.mysql import get_connection, get_creator, delete_upload_job
from collections import OrderedDict

creator_report_bp = Blueprint(
    "creator_report",
    __name__,
    url_prefix="/creator"
)

# ==============================
# KONSTANTA NAMA HARI & BULAN
# ==============================
NAMA_HARI_MAP = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis",
                 4: "Jumat", 5: "Sabtu", 6: "Minggu"}
NAMA_BULAN_MAP = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                  5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                  9: "September", 10: "Oktober", 11: "November", 12: "Desember"}

# ==============================
# STATUS MAPPINGS
# ==============================
BADGE_MAP = {
    "uploaded":  ("bg-green-lt text-green",  "ti-circle-check",  "Uploaded"),
    "scheduled": ("bg-blue-lt text-blue",    "ti-calendar-time", "Scheduled"),
    "pending":   ("bg-yellow-lt text-yellow","ti-clock",         "Pending"),
    "failed":    ("bg-red-lt text-red",      "ti-alert-circle",  "Failed"),
    "cancelled": ("bg-secondary-lt",         "ti-x",             "Cancelled"),
}
BADGE_DEFAULT = ("bg-secondary-lt", "ti-question-mark", "Unknown")


def _format_datetime(dt):
    """Format datetime object ke string."""
    if isinstance(dt, (datetime.datetime, datetime.date)):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt)


def _get_folder_name(full_path):
    """Ambil nama folder terakhir dari path."""
    if not full_path:
        return ""
    path = full_path.replace("\\", "/")
    parts = path.rstrip("/").split("/")
    return parts[-1] if parts else full_path


_SCHEDULE_FOLDER_PATTERN = re.compile(r"^\d{4}_\d{2}_\d{2}_\d{2}_\d{2}$")


def _is_schedule_folder(path):
    """Cek apakah path menunjuk ke folder schedule (leaf %Y_%m_%d_%H_%M)."""
    if not path:
        return False
    leaf = os.path.basename(path.rstrip("\\/"))
    return bool(_SCHEDULE_FOLDER_PATTERN.match(leaf))


def _compute_display_status(db_status, schedule_datetime, now):
    """
    Hitung status yang sebenarnya ditampilkan.

    Aturan:
    - Jika database = 'uploaded' DAN schedule_datetime > now → 'scheduled'
    - Jika database = 'uploaded' DAN schedule_datetime <= now → 'uploaded'
    - Selain itu, gunakan status database langsung.

    Returns:
        str: display_status ('uploaded', 'scheduled', 'pending', 'failed', 'cancelled', 'unknown')
    """
    if db_status == "uploaded" and schedule_datetime > now:
        return "scheduled"
    return db_status


def _get_badge(display_status):
    """Ambil tuple (badge_class, icon, label) untuk status display."""
    return BADGE_MAP.get(display_status, BADGE_DEFAULT)


def _build_tooltip_text(item):
    """Buat tooltip HTML string dari data upload item.

    Gunakan single quote (') untuk atribut HTML di dalam string.
    JANGAN gunakan &quot; karena menyebabkan TemplateSyntaxError.
    """
    lines = [
        "<div class='text-start'>",
        f"<strong>{item['product_name']}</strong><br>",
        f"Product ID: {item['product_id']}<br>",
        f"Schedule: {item['schedule_datetime']}<br>",
        f"Status: {item['status_badge_label']}<br>",
        f"Folder: {item['folder_name']}<br>",
        f"Retry: {item['retry_count']}x",
    ]
    if item.get("uploaded_at"):
        lines.append(f"<br>Uploaded at: {item['uploaded_at']}")
    lines.append("</div>")
    return " ".join(lines)


def get_creator_upload_schedule(creator_id: int):
    """
    Ambil seluruh jadwal upload untuk satu Creator.

    Logika:
    1. Query database ORDER BY schedule_datetime DESC (descending)
    2. Hitung display_status untuk setiap item:
       - Jika DB='uploaded' & schedule > now → 'scheduled'
       - Jika DB='uploaded' & schedule <= now → 'uploaded'
       - Selain itu → status DB langsung
    3. Filter histori: item dengan display_status='uploaded' hanya ditampilkan
       jika schedule_datetime >= (now - 8 hari). Item dengan status lain tetap tampil.
    4. Kelompokkan per tanggal, beri ringkasan.
    5. Semua data siap render, template hanya loop + render.

    Returns:
        dict or None
    """
    creator = get_creator(creator_id)
    if not creator:
        return None

    now = datetime.datetime.now()
    # Batas 8 hari untuk status Uploaded
    batas_8_hari = now - datetime.timedelta(days=8)

    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            sql = """
                SELECT
                    uj.id,
                    uj.creator_id,
                    uj.batch_id,
                    uj.product_id,
                    uj.schedule_datetime,
                    uj.folder,
                    uj.status,
                    uj.retry_count,
                    uj.uploaded_at,
                    uj.updated_at,
                    uj.created_at,
                    tp.id AS product_db_id,
                    tp.tiktok_id_product,
                    tp.title AS product_title
                FROM upload_jobs uj
                LEFT JOIN tiktok_products tp
                    ON tp.tiktok_id_product = uj.product_id
                WHERE uj.creator_id = %s
                ORDER BY uj.schedule_datetime DESC
            """

            cursor.execute(sql, (creator_id,))
            rows = cursor.fetchall()

    finally:
        conn.close()

    if not rows:
        return {
            "creator": creator,
            "total_jadwal": 0,
            "total_uploaded": 0,
            "total_scheduled": 0,
            "total_pending": 0,
            "total_failed": 0,
            "upload_progress": 0,
            "tanggal_pertama": None,
            "tanggal_terakhir": None,
            "rata_rata_per_hari": 0,
            "days": []
        }

    days_map = OrderedDict()
    all_items = []  # Untuk akumulasi setelah filter

    total = 0
    total_uploaded = 0
    total_scheduled = 0
    total_pending = 0
    total_failed = 0
    tanggal_pertama = None
    tanggal_terakhir = None

    for row in rows:
        # ==============================
        # PARSE SCHEDULE DATETIME
        # ==============================
        sched = row["schedule_datetime"]
        if isinstance(sched, (datetime.datetime, datetime.date)):
            sched_dt = sched
        elif isinstance(sched, str):
            try:
                sched_dt = datetime.datetime.strptime(sched, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        else:
            continue

        # ==============================
        # HITUNG DISPLAY STATUS
        # ==============================
        db_status = row.get("status", "unknown")
        display_status = _compute_display_status(db_status, sched_dt, now)
        badge_class, badge_icon, badge_label = _get_badge(display_status)

        # ==============================
        # FILTER HISTORI (hanya untuk uploaded)
        # ==============================
        if display_status == "uploaded" and sched_dt < batas_8_hari:
            # Uploaded yang sudah lebih dari 8 hari → skip
            continue

        # ==============================
        # FORMAT TANGGAL
        # ==============================
        tgl_key = sched_dt.strftime("%Y-%m-%d")
        jam_str = sched_dt.strftime("%H:%M")
        sched_formatted = sched_dt.strftime("%Y-%m-%d %H:%M:%S")

        hari_index = sched_dt.weekday()
        nama_hari = NAMA_HARI_MAP.get(hari_index, "")
        nama_bulan = NAMA_BULAN_MAP.get(sched_dt.month, str(sched_dt.month))
        tanggal_formatted = f"{sched_dt.day} {nama_bulan} {sched_dt.year}"

        # ==============================
        # INIT DAY MAP
        # ==============================
        if tgl_key not in days_map:
            days_map[tgl_key] = {
                "tanggal": tgl_key,
                "nama_hari": nama_hari,
                "tanggal_formatted": tanggal_formatted,
                "uploads": [],
                "summary": {"total": 0, "uploaded": 0, "scheduled": 0,
                            "pending": 0, "failed": 0, "cancelled": 0, "unknown": 0}
            }

        # ==============================
        # PROSES FIELD
        # ==============================
        tiktok_id = row.get("tiktok_id_product")
        product_title = row.get("product_title")
        if not product_title:
            product_title = f"Product #{row.get('product_id', '?')}"

        thumbnail = None
        if tiktok_id:
            thumbnail = f"/static/products/{tiktok_id}/product/1.jpg"

        folder_name = _get_folder_name(row.get("folder", ""))

        uploaded_at_formatted = None
        if row.get("uploaded_at"):
            uploaded_at_formatted = _format_datetime(row["uploaded_at"])

        product_url = f"/product/{row['product_id']}"

        # ==============================
        # BUILD UPLOAD ITEM (siap render)
        # ==============================
        schedule_display = (
            f"{sched_dt.day} {NAMA_BULAN_MAP.get(sched_dt.month, sched_dt.month)} "
            f"{sched_dt.year} {jam_str}"
        )

        upload_item = {
            "jam_upload": jam_str,
            "schedule_datetime": sched_formatted,
            "schedule_display": schedule_display,
            "product_name": product_title,
            "product_id": row.get("product_id"),
            "product_url": product_url,
            "thumbnail": thumbnail,
            "display_status": display_status,
            "status_badge_class": badge_class,
            "status_badge_icon": badge_icon,
            "status_badge_label": badge_label,
            "folder_name": folder_name,
            "folder_path": row.get("folder") or "",
            "upload_job_id": row.get("id"),
            "retry_count": row.get("retry_count", 0),
            "uploaded_at": uploaded_at_formatted,
        }
        upload_item["tooltip_text"] = _build_tooltip_text(upload_item)

        # ==============================
        # POPULATE
        # ==============================
        days_map[tgl_key]["uploads"].append(upload_item)
        all_items.append(upload_item)

        # ==============================
        # UPDATE RINGKASAN PER HARI
        # ==============================
        days_map[tgl_key]["summary"]["total"] += 1
        if display_status in days_map[tgl_key]["summary"]:
            days_map[tgl_key]["summary"][display_status] += 1

        # ==============================
        # UPDATE TOTAL GLOBAL
        # ==============================
        total += 1
        if display_status == "uploaded":
            total_uploaded += 1
        elif display_status == "scheduled":
            total_scheduled += 1
        elif display_status == "pending":
            total_pending += 1
        elif display_status == "failed":
            total_failed += 1

        # Track first & last date (dengan data DESC, pertama = terbaru)
        if tanggal_pertama is None or tgl_key < tanggal_pertama:
            tanggal_pertama = tgl_key
        if tanggal_terakhir is None or tgl_key > tanggal_terakhir:
            tanggal_terakhir = tgl_key

    # ==============================
    # HITUNG PROGRESS
    # upload_progress = (uploaded + scheduled) / total * 100
    # Uploaded = sudah tayang. Scheduled = sudah diupload tapi belum jadwal tayang.
    # Keduanya dianggap "berhasil dikirim".
    # ==============================
    berhasil = total_uploaded + total_scheduled
    upload_progress = 0
    if total > 0:
        upload_progress = round((berhasil / total) * 100)

    # ==============================
    # RATA-RATA PER HARI
    # ==============================
    rata_rata = 0
    if days_map:
        total_hari = len(days_map)
        rata_rata = round(total / total_hari, 1)

    # days_map sudah DESC karena query ORDER BY schedule_datetime DESC
    # Tapi OrderedDict tetap dalam urutan insert (terbaru duluan)

    # ==============================
    # URUTKAN UPLOAD PER TANGGAL (ASCENDING)
    # Setiap grup tanggal harus ascending berdasarkan schedule_datetime
    # ==============================
    for day in days_map.values():
        day["uploads"].sort(key=lambda x: x["schedule_datetime"])

    return {
        "creator": creator,
        "total_jadwal": total,
        "total_uploaded": total_uploaded,
        "total_scheduled": total_scheduled,
        "total_pending": total_pending,
        "total_failed": total_failed,
        "upload_progress": upload_progress,
        "tanggal_pertama": tanggal_pertama,
        "tanggal_terakhir": tanggal_terakhir,
        "rata_rata_per_hari": rata_rata,
        "days": list(days_map.values())
    }


@creator_report_bp.route("/<int:creator_id>/report")
def creator_report(creator_id):
    """
    Halaman report jadwal upload untuk satu Creator.
    URL: /creator/<creator_id>/report
    """
    data = get_creator_upload_schedule(creator_id)

    if data is None:
        abort(404, description="Creator tidak ditemukan")

    creator = data["creator"]

    return render_template(
        "creator/report.html",
        page_title=f"Upload Schedule - {creator.get('display_name', creator.get('username', 'Unknown'))}",
        report_data=data
    )


@creator_report_bp.route("/<int:creator_id>/report/remove_schedule", methods=["POST"])
def remove_schedule(creator_id):
    """
    Hapus schedule upload (record database + folder schedule di disk).

    Proses:
    1. Validasi upload job milik creator.
    2. Hapus record upload_jobs dari database.
    3. Hapus folder schedule secara recursive (hanya folder schedule yang valid).
    """
    payload = request.get_json(silent=True) or {}
    job_id = payload.get("job_id")

    if not job_id:
        return jsonify({"success": False, "message": "job_id tidak ditemukan."})

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, folder
                FROM upload_jobs
                WHERE id = %s AND creator_id = %s
                LIMIT 1
                """,
                (job_id, creator_id)
            )
            row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({"success": False, "message": "Upload job tidak ditemukan."})

    folder = row.get("folder") or ""

    # 1. Hapus record database
    if not delete_upload_job(job_id):
        return jsonify({"success": False, "message": "Gagal menghapus data schedule dari database."})

    # 2. Hapus folder schedule dari disk (recursive)
    notes = []
    if folder:
        if not os.path.isdir(folder):
            notes.append("Folder schedule sudah tidak ada di disk.")
        elif not _is_schedule_folder(folder):
            notes.append("Folder tidak dihapus karena bukan folder schedule yang valid.")
        else:
            try:
                shutil.rmtree(folder)
            except Exception as e:
                return jsonify({
                    "success": False,
                    "message": "Data schedule terhapus, tetapi gagal menghapus folder: " + str(e)
                })

    message = "Schedule berhasil dihapus."
    if notes:
        message += " " + " ".join(notes)

    return jsonify({"success": True, "message": message})


# ==============================
# BULK DELETE UPLOAD JOBS (fitur baru)
# ==============================

def _bulk_delete_pending_jobs(creator_id, job_ids):
    """
    Hapus banyak upload_jobs (status pending SAJA) milik creator dalam satu
    transaction, lalu bersihkan schedule_batches yang sudah tidak memiliki
    upload_jobs.

    Aturan:
    - Data job diambil langsung dari database (id, batch_id, status, folder).
    - Hanya status 'pending' yang diproses; scheduled/uploaded diabaikan.
    - schedule_batches dihapus HANYA jika COUNT(upload_jobs) per batch = 0.

    Returns:
        dict atau None (None = error database, transaction di-rollback):
        {
            "deleted_ids": [int],
            "skipped_ids": [int],
            "removed_batches": [int],
            "folders": [str],
        }
    """
    placeholders = ", ".join(["%s"] * len(job_ids))
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Ambil data langsung dari database (JANGAN percaya path frontend)
            cursor.execute(
                f"""
                SELECT id, batch_id, status, folder
                FROM upload_jobs
                WHERE creator_id = %s AND id IN ({placeholders})
                """,
                [creator_id] + list(job_ids)
            )
            rows = cursor.fetchall()

            pending_ids = [r["id"] for r in rows if r.get("status") == "pending"]
            skipped_ids = [r["id"] for r in rows if r.get("status") != "pending"]
            batch_ids = sorted({
                r["batch_id"]
                for r in rows
                if r.get("status") == "pending" and r.get("batch_id")
            })
            folders = [
                r["folder"]
                for r in rows
                if r.get("status") == "pending" and r.get("folder")
            ]

            if not pending_ids:
                return {
                    "deleted_ids": [],
                    "skipped_ids": skipped_ids,
                    "removed_batches": [],
                    "folders": [],
                }

            # 2. Hapus job yang valid (pending + milik creator).
            #    Filter status='pending' diulang di SQL sebagai double-check.
            del_placeholders = ", ".join(["%s"] * len(pending_ids))
            cursor.execute(
                f"""
                DELETE FROM upload_jobs
                WHERE creator_id = %s
                  AND status = 'pending'
                  AND id IN ({del_placeholders})
                """,
                [creator_id] + pending_ids
            )

            # 3. Bersihkan schedule_batches yang sudah tidak punya upload_jobs.
            removed_batches = []
            for batch_id in batch_ids:
                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM upload_jobs WHERE batch_id = %s",
                    (batch_id,)
                )
                cnt = cursor.fetchone()["cnt"]
                if cnt == 0:
                    cursor.execute(
                        "DELETE FROM schedule_batches WHERE id = %s AND creator_id = %s",
                        (batch_id, creator_id)
                    )
                    removed_batches.append(batch_id)

        conn.commit()

        return {
            "deleted_ids": pending_ids,
            "skipped_ids": skipped_ids,
            "removed_batches": removed_batches,
            "folders": folders,
        }

    except Exception as e:
        conn.rollback()
        print(f"_bulk_delete_pending_jobs() error: {e}")
        return None
    finally:
        conn.close()


def _is_job_folder(path):
    """
    Validasi folder job: leaf DAN parent-nya harus folder schedule
    (%Y_%m_%d_%H_%M). Folder job selalu berada DI DALAM folder batch,
    sehingga struktur depth-2 ini memastikan yang dihapus adalah folder
    job (leaf), bukan folder batch atau direktori di atasnya.
    """
    if not path:
        return False
    path = os.path.normpath(path)
    if not _is_schedule_folder(path):
        return False
    parent = os.path.dirname(path)
    return bool(parent) and _is_schedule_folder(parent)


def _delete_job_folders(folders):
    """
    Hapus folder project/job dari disk (opsional, delete_folders=true).

    Hanya path yang berasal dari database yang diproses. Path dari request
    frontend TIDAK PERNAH dipakai. Mengembalikan list catatan (notes).
    """
    notes = []
    for folder in folders or []:
        if not folder:
            continue
        if not os.path.isdir(folder):
            notes.append(f"Folder {folder} sudah tidak ada di disk.")
            continue
        if not _is_job_folder(folder):
            notes.append(
                f"Folder {folder} tidak dihapus karena bukan folder job yang valid."
            )
            continue
        try:
            shutil.rmtree(folder)
        except Exception as e:
            notes.append(f"Gagal menghapus folder {folder}: {e}")
    return notes


@creator_report_bp.route("/<int:creator_id>/report/bulk_delete", methods=["POST"])
def bulk_delete_upload_jobs(creator_id):
    """
    Bulk delete upload jobs (hanya status pending) milik creator.

    Request JSON:
        {"job_ids": [101, 102, 103], "delete_folders": false}

    - Data job dibaca dari database berdasarkan job_ids (folder path dari DB).
    - Hanya job status 'pending' yang diproses; scheduled/uploaded tetap aman.
    - schedule_batches yang sudah tidak memiliki upload_jobs ikut dihapus.
    - delete_folders (default false) menghapus folder project/job dari disk
      dengan validasi ketat (folder job, bukan folder parent).
    """
    payload = request.get_json(silent=True) or {}
    raw_ids = payload.get("job_ids")
    delete_folders = bool(payload.get("delete_folders", False))

    try:
        job_ids = [int(x) for x in raw_ids]
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "job_ids tidak valid."})

    if not job_ids:
        return jsonify({"success": False, "message": "Tidak ada job yang dipilih."})

    result = _bulk_delete_pending_jobs(creator_id, job_ids)
    if result is None:
        return jsonify({
            "success": False,
            "message": "Terjadi kesalahan saat menghapus data dari database.",
        })

    deleted_ids = result["deleted_ids"]
    if not deleted_ids:
        message = "Tidak ada upload job yang bisa dihapus (hanya status pending yang diizinkan)."
        if result["skipped_ids"]:
            message += " Job dengan status selain pending diabaikan."
        return jsonify({"success": False, "message": message})

    notes = []
    if delete_folders:
        notes.extend(_delete_job_folders(result["folders"]))

    message = f"{len(deleted_ids)} upload job berhasil dihapus."
    if result["removed_batches"]:
        message += f" {len(result['removed_batches'])} batch kosong ikut dihapus."
    if result["skipped_ids"]:
        message += (
            f" {len(result['skipped_ids'])} job diabaikan "
            f"karena bukan status pending."
        )
    if notes:
        message += " " + " ".join(notes)

    return jsonify({
        "success": True,
        "message": message,
        "deleted_ids": deleted_ids,
    })
