from flask import Blueprint, render_template, abort
from includes.mysql import get_connection, get_creator
from collections import OrderedDict
import datetime

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
        upload_item = {
            "jam_upload": jam_str,
            "schedule_datetime": sched_formatted,
            "product_name": product_title,
            "product_id": row.get("product_id"),
            "product_url": product_url,
            "thumbnail": thumbnail,
            "display_status": display_status,
            "status_badge_class": badge_class,
            "status_badge_icon": badge_icon,
            "status_badge_label": badge_label,
            "folder_name": folder_name,
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
