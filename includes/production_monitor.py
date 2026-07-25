# File: includes/production_monitor.py
# Database layer untuk modul Monitor Produksi
# Semua query SQL ada di sini, bukan di router atau template.

from datetime import datetime
from includes.mysql import get_connection


# ==============================
# KONSTANTA
# ==============================
BOBOT_FAILED = 1000
BOBOT_SISA_HARI = 1
BATAS_AMAN = 14
BATAS_SIAPKAN_BATCH = 7
BATAS_PRODUKSI = 3
HARI_IDEAL_MAX = 30
MAKSIMAL_TUGAS = 5


def get_now():
    return datetime.now()


# ==============================
# HELPER
# ==============================

def _hitung_priority_score(upload_gagal: int, sisa_hari) -> int:
    """Semakin tinggi score, semakin prioritas."""
    score = upload_gagal * BOBOT_FAILED
    if sisa_hari is not None:
        score += (BATAS_AMAN - min(sisa_hari, BATAS_AMAN)) * BOBOT_SISA_HARI
    else:
        score += BATAS_AMAN * BOBOT_SISA_HARI
    return score


def _tentukan_status(sisa_hari, upload_gagal):
    """(label, color)
    Label: KRITIS, PRODUKSI, PERSIAPAN, AMAN"""
    if upload_gagal > 0:
        return "KRITIS", "bg-red"
    if sisa_hari is None or sisa_hari < BATAS_PRODUKSI:
        return "KRITIS", "bg-red"
    if sisa_hari < BATAS_SIAPKAN_BATCH:
        return "PRODUKSI", "bg-orange"
    if sisa_hari < BATAS_AMAN:
        return "PERSIAPAN", "bg-blue"
    return "AMAN", "bg-green"


def _format_hari(sisa_hari) -> str:
    """Format sisa hari ke kalimat natural."""
    if sisa_hari is None or sisa_hari < 0:
        return "hari ini"
    if sisa_hari == 0:
        return "hari ini"
    if sisa_hari == 1:
        return "besok"
    return f"{sisa_hari} hari lagi"


# ==============================
# SUMMARY
# ==============================

def get_summary():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            now = get_now()

            cursor.execute("SELECT COUNT(*) AS cnt FROM creators WHERE is_active=1")
            total_creators = cursor.fetchone()["cnt"]

            cursor.execute("""
                SELECT COUNT(*) AS cnt
                FROM upload_jobs
                WHERE schedule_datetime >= %s AND status != 'failed'
            """, (now,))
            total_persediaan = cursor.fetchone()["cnt"]

            cursor.execute("""
                SELECT COUNT(DISTINCT c.id) AS cnt
                FROM creators c
                LEFT JOIN upload_jobs uj ON uj.creator_id = c.id
                    AND uj.schedule_datetime >= %s AND uj.status != 'failed'
                LEFT JOIN upload_jobs uj_f ON uj_f.creator_id = c.id
                    AND uj_f.status = 'failed'
                WHERE c.is_active = 1
                GROUP BY c.id
                HAVING
                    COUNT(DISTINCT uj_f.id) > 0
                    OR MAX(uj.schedule_datetime) IS NULL
                    OR DATEDIFF(MAX(uj.schedule_datetime), %s) < %s
            """, (now, now, BATAS_PRODUKSI))
            total_prioritas = len(cursor.fetchall())

            cursor.execute("SELECT COUNT(*) AS cnt FROM upload_jobs WHERE status='pending'")
            total_belum_upload = cursor.fetchone()["cnt"]

            cursor.execute("""
                SELECT COUNT(*) AS cnt
                FROM upload_jobs
                WHERE status = 'uploaded' AND schedule_datetime > %s
            """, (now,))
            total_video_terjadwal = cursor.fetchone()["cnt"]

            cursor.execute("""
                SELECT MAX(schedule_datetime) AS jadwal_terakhir
                FROM upload_jobs
                WHERE status = 'uploaded'
            """)
            row = cursor.fetchone()
            jadwal_terakhir = row["jadwal_terakhir"]
            sisa_hari_global = max(0, (jadwal_terakhir - now).days) if jadwal_terakhir else 0

            cursor.execute("""
                SELECT MAX(schedule_datetime) AS persediaan_sampai
                FROM upload_jobs
                WHERE status IN ('pending', 'uploaded')
            """)
            row = cursor.fetchone()
            persediaan_sampai = row["persediaan_sampai"]

            cursor.execute("SELECT COUNT(*) AS cnt FROM upload_jobs WHERE status='failed'")
            total_gagal = cursor.fetchone()["cnt"]

        return {
            "total_creators": total_creators,
            "total_persediaan": total_persediaan,
            "total_belum_upload": total_belum_upload,
            "total_video_terjadwal": total_video_terjadwal,
            "sisa_hari_global": sisa_hari_global,
            "total_prioritas": total_prioritas,
            "total_gagal": total_gagal,
            "persediaan_sampai": persediaan_sampai,
        }
    finally:
        conn.close()


# ==============================
# FOKUS HARI INI (Hero Card)
# ==============================

def get_fokus_hari_ini():
    """
    Satu creator paling kritis untuk ditampilkan di Hero Card.

    Returns:
        dict or None: {
            "id", "display_name", "username",
            "sisa_hari", "jadwal_terakhir", "persediaan_video",
            "upload_gagal", "status_label", "status_color",
            "pesan_fokus", "target_hari_ini", "tombol_label"
        }
    """
    all_creators = get_creator_status()
    if not all_creators:
        return None

    # Cari creator paling prioritas yang KRITIS
    for c in all_creators:
        if c["status_label"] in ("KRITIS", "PRODUKSI"):
            return _build_fokus(c)

    # Jika semua aman, ambil yang paling mendekati habis
    creator_terdekat = all_creators[-1]  # score terendah = paling aman? No, sorted desc
    # all_creators sorted desc by priority_score, jadi yang terakhir adalah paling aman.
    # Tapi kita ingin creator dengan sisa_hari terkecil di antara yang aman
    creator_terdekat = min(all_creators, key=lambda x: (x["sisa_hari"] if x["sisa_hari"] is not None else 999))
    if creator_terdekat["sisa_hari"] is not None and creator_terdekat["sisa_hari"] >= BATAS_AMAN:
        return {
            "aman_semua": True,
            "creator_terdekat": creator_terdekat["display_name"],
            "sisa_hari_terdekat": creator_terdekat["sisa_hari"],
        }

    return _build_fokus(creator_terdekat)


def _build_fokus(creator):
    """Bangun data untuk Hero Card dari satu creator."""
    sisa = creator["sisa_hari"]
    jt = creator["jadwal_terakhir"]
    gagal = creator["upload_gagal"]
    label = creator["status_label"]

    if gagal > 0:
        pesan = f"{gagal} video gagal dijadwalkan"
        target = "Upload Ulang Video"
        tombol = "Retry Upload"
        tombol_icon = "ti ti-refresh"
    elif sisa is None or sisa <= 0:
        pesan = "Persediaan video sudah habis"
        target = "Produksi Batch Baru"
        tombol = "Buat Batch Baru"
        tombol_icon = "ti ti-plus"
    elif sisa < BATAS_PRODUKSI:
        pesan = f"Video cukup sampai {jt.strftime('%d %B %Y')} ({_format_hari(sisa)})"
        target = "Produksi Batch Baru"
        tombol = "Buat Batch Baru"
        tombol_icon = "ti ti-plus"
    elif sisa < BATAS_SIAPKAN_BATCH:
        pesan = f"Video akan habis dalam {_format_hari(sisa)}"
        target = "Siapkan Batch Baru"
        tombol = "Buat Batch Baru"
        tombol_icon = "ti ti-calendar-plus"
    else:
        pesan = f"Persediaan masih {sisa} hari"
        target = "Pantau Persediaan"
        tombol = "Lihat Detail"
        tombol_icon = "ti ti-eye"

    return {
        "aman_semua": False,
        "id": creator["id"],
        "display_name": creator["display_name"],
        "username": creator["username"],
        "profile_image": creator["profile_image"],
        "sisa_hari": sisa,
        "jadwal_terakhir": jt,
        "persediaan_video": creator.get("video_belum_upload", 0),
        "upload_gagal": gagal,
        "status_label": label,
        "status_color": creator["status_color"],
        "pesan_fokus": pesan,
        "target_hari_ini": target,
        "tombol_label": tombol,
        "tombol_icon": tombol_icon,
    }


# ==============================
# CREATOR STATUS
# ==============================

def get_creator_status():
    """
    Semua creator aktif dengan Priority Score.
    Diurutkan dari score tertinggi (paling prioritas).

    Returns:
        list[dict]
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            now = get_now()

            cursor.execute("""
                SELECT
                    c.id,
                    c.username,
                    c.display_name,
                    c.profile_image,
                    COUNT(DISTINCT CASE
                        WHEN uj.status = 'pending'
                        THEN uj.id
                    END) AS video_belum_upload,
                    COUNT(DISTINCT CASE
                        WHEN uj.status = 'uploaded' AND uj.schedule_datetime > %s
                        THEN uj.id
                    END) AS video_terjadwal,
                    MAX(CASE
                        WHEN uj.status = 'uploaded'
                        THEN uj.schedule_datetime
                    END) AS jadwal_terakhir,
                    MIN(CASE
                        WHEN uj.status = 'uploaded'
                        THEN uj.schedule_datetime
                    END) AS upload_berikutnya,
                    COUNT(DISTINCT CASE
                        WHEN uj.status = 'failed' THEN uj.id
                    END) AS upload_gagal
                FROM creators c
                LEFT JOIN upload_jobs uj ON uj.creator_id = c.id
                WHERE c.is_active = 1
                GROUP BY c.id, c.username, c.display_name, c.profile_image
            """, (now,))

            rows = cursor.fetchall()

        results = []
        for row in rows:
            jadwal_terakhir = row["jadwal_terakhir"]
            upload_gagal = row["upload_gagal"] or 0
            sisa_hari = max(0, (jadwal_terakhir - now).days) if jadwal_terakhir else 0

            status_label, status_color = _tentukan_status(sisa_hari, upload_gagal)
            priority_score = _hitung_priority_score(upload_gagal, sisa_hari)

            video_belum_upload = row["video_belum_upload"] or 0
            video_terjadwal = row["video_terjadwal"] or 0

            if video_belum_upload > 0 or video_terjadwal > 0:
                rentang_full = video_belum_upload + video_terjadwal
                progress_persen = min(round((rentang_full / HARI_IDEAL_MAX) * 100), 100)
            else:
                rentang_full = 0
                progress_persen = 0

            results.append({
                "id": row["id"],
                "username": row["username"],
                "display_name": row["display_name"] or row["username"],
                "profile_image": row["profile_image"],
                "video_belum_upload": video_belum_upload,
                "video_terjadwal": video_terjadwal,
                "upload_berikutnya": row["upload_berikutnya"],
                "jadwal_terakhir": jadwal_terakhir,
                "sisa_hari": sisa_hari,
                "upload_gagal": upload_gagal,
                "status_label": status_label,
                "status_color": status_color,
                "priority_score": priority_score,
                "rentang_hari": rentang_full,
                "progress_persen": progress_persen,
            })

        results.sort(key=lambda x: x["priority_score"], reverse=True)
        return results
    finally:
        conn.close()


# ==============================
# TUGAS HARI INI (daftar pekerjaan)
# ==============================

def get_tugas_hari_ini():
    """
    Daftar pekerjaan terstruktur dengan jenis, alasan, dan tombol aksi.
    Maksimal MAKSIMAL_TUGAS item.
    Jika lebih, template akan menampilkan "Lihat Semua".

    Setiap tugas punya:
    - jenis: "upload_ulang" | "produksi_video" | "buat_batch"
    - icon, icon_color (berbeda tiap jenis)
    - creator_id, creator_name, creator_username
    - alasan (kalimat jelas mengapa)
    - badge_label, badge_color: KRITIS/PRODUKSI/PERSIAPAN/AMAN
    - tombol_label, tombol_icon, tombol_disabled: bool
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            now = get_now()
            tugas = []

            # ========================
            # 1. UPLOAD ULANG (gagal)
            # ========================
            cursor.execute("""
                SELECT c.id, c.display_name, c.username, COUNT(*) AS jml
                FROM upload_jobs uj
                JOIN creators c ON c.id = uj.creator_id
                WHERE uj.status = 'failed'
                GROUP BY c.id, c.display_name, c.username
                ORDER BY jml DESC
            """)
            for r in cursor.fetchall():
                nama = r["display_name"] or r["username"]
                tugas.append({
                    "jenis": "upload_ulang",
                    "icon": "ti ti-refresh",
                    "icon_color": "text-warning",
                    "creator_id": r["id"],
                    "creator_name": nama,
                    "creator_username": r["username"],
                    "alasan": f"{r['jml']} video gagal dijadwalkan",
                    "badge_label": "KRITIS",
                    "badge_color": "bg-red",
                    "tombol_label": "Retry Upload",
                    "tombol_icon": "ti ti-refresh",
                    "tombol_disabled": True,
                    "prioritas": 1,
                })

            # ========================
            # 2. PRODUKSI VIDEO (sisa < 3 atau tanpa jadwal)
            # ========================
            cursor.execute("""
                SELECT
                    c.id, c.display_name, c.username,
                    MAX(CASE
                        WHEN uj.schedule_datetime >= %s AND uj.status != 'failed'
                        THEN uj.schedule_datetime
                    END) AS jadwal_terakhir,
                    COUNT(DISTINCT CASE
                        WHEN uj.schedule_datetime >= %s AND uj.status != 'failed'
                        THEN uj.id
                    END) AS persediaan_video
                FROM creators c
                LEFT JOIN upload_jobs uj ON uj.creator_id = c.id
                    AND uj.schedule_datetime >= %s AND uj.status != 'failed'
                WHERE c.is_active = 1
                GROUP BY c.id, c.display_name, c.username
            """, (now, now, now))
            for r in cursor.fetchall():
                nama = r["display_name"] or r["username"]
                jt = r["jadwal_terakhir"]
                sisa = (jt - now).days if jt else None

                # Skip jika sudah ada tugas gagal untuk creator ini
                if any(t["creator_id"] == r["id"] and t["jenis"] == "upload_ulang" for t in tugas):
                    continue

                # Hanya yang KRITIS (sisa < 3 atau tanpa jadwal)
                if sisa is not None and sisa >= BATAS_PRODUKSI:
                    continue

                if sisa is None:
                    alasan = "Belum memiliki jadwal produksi"
                elif sisa < 0:
                    alasan = "Persediaan video sudah habis"
                elif sisa == 0:
                    alasan = "Video akan habis hari ini"
                elif sisa == 1:
                    alasan = "Video cukup sampai besok"
                else:
                    alasan = f"Video cukup sampai {jt.strftime('%d %B %Y')} ({_format_hari(sisa)})"

                tugas.append({
                    "jenis": "produksi_video",
                    "icon": "ti ti-player-play",
                    "icon_color": "text-danger",
                    "creator_id": r["id"],
                    "creator_name": nama,
                    "creator_username": r["username"],
                    "alasan": alasan,
                    "badge_label": "KRITIS",
                    "badge_color": "bg-red",
                    "tombol_label": "Buat Batch Baru",
                    "tombol_icon": "ti ti-plus",
                    "tombol_disabled": True,
                    "prioritas": 2,
                })

            # ========================
            # 3. PRODUKSI (sisa 3-7)
            # ========================
            cursor.execute("""
                SELECT c.id, c.display_name, c.username,
                       DATEDIFF(MAX(CASE WHEN uj.schedule_datetime >= %s AND uj.status != 'failed' THEN uj.schedule_datetime END), %s) AS sisa_hari
                FROM creators c
                LEFT JOIN upload_jobs uj ON uj.creator_id = c.id AND uj.schedule_datetime >= %s AND uj.status != 'failed'
                WHERE c.is_active = 1
                GROUP BY c.id, c.display_name, c.username
                HAVING sisa_hari >= %s AND sisa_hari < %s
                ORDER BY sisa_hari ASC
            """, (now, now, now, BATAS_PRODUKSI, BATAS_SIAPKAN_BATCH))
            for r in cursor.fetchall():
                nama = r["display_name"] or r["username"]
                sisa = r["sisa_hari"]
                tugas.append({
                    "jenis": "produksi_video",
                    "icon": "ti ti-player-play",
                    "icon_color": "text-orange",
                    "creator_id": r["id"],
                    "creator_name": nama,
                    "creator_username": r["username"],
                    "alasan": f"Video akan habis dalam {_format_hari(sisa)}",
                    "badge_label": "PRODUKSI",
                    "badge_color": "bg-orange",
                    "tombol_label": "Buat Batch Baru",
                    "tombol_icon": "ti ti-plus",
                    "tombol_disabled": True,
                    "prioritas": 3,
                })

            # ========================
            # 4. PERSIAPAN BATCH (sisa 7-14)
            # ========================
            cursor.execute("""
                SELECT c.id, c.display_name, c.username,
                       DATEDIFF(MAX(CASE WHEN uj.schedule_datetime >= %s AND uj.status != 'failed' THEN uj.schedule_datetime END), %s) AS sisa_hari
                FROM creators c
                LEFT JOIN upload_jobs uj ON uj.creator_id = c.id AND uj.schedule_datetime >= %s AND uj.status != 'failed'
                WHERE c.is_active = 1
                GROUP BY c.id, c.display_name, c.username
                HAVING sisa_hari >= %s AND sisa_hari < %s
                ORDER BY sisa_hari ASC
            """, (now, now, now, BATAS_SIAPKAN_BATCH, BATAS_AMAN))
            for r in cursor.fetchall():
                nama = r["display_name"] or r["username"]
                sisa = r["sisa_hari"]
                tugas.append({
                    "jenis": "buat_batch",
                    "icon": "ti ti-calendar-plus",
                    "icon_color": "text-blue",
                    "creator_id": r["id"],
                    "creator_name": nama,
                    "creator_username": r["username"],
                    "alasan": f"Persediaan tinggal {_format_hari(sisa)}. Segera siapkan batch baru.",
                    "badge_label": "PERSIAPAN",
                    "badge_color": "bg-blue",
                    "tombol_label": "Buat Batch",
                    "tombol_icon": "ti ti-calendar-plus",
                    "tombol_disabled": True,
                    "prioritas": 4,
                })

        # Urut berdasarkan prioritas, batasi
        tugas.sort(key=lambda x: x["prioritas"])

        # Cek apakah perlu tombol "Lihat Semua"
        ada_lebih = len(tugas) > MAKSIMAL_TUGAS
        tugas_tampil = tugas[:MAKSIMAL_TUGAS]

        return {
            "tugas": tugas_tampil,
            "total_semua": len(tugas),
            "ada_lebih": ada_lebih,
        }
    finally:
        conn.close()


# ==============================
# BATCH AKTIF
# ==============================

def get_active_batches():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    sb.id AS batch_id,
                    c.display_name AS creator_name,
                    c.username AS creator_username,
                    sb.start_datetime,
                    sb.finish_datetime,
                    sb.total_jobs,
                    COUNT(uj.id) AS total_terisi,
                    SUM(CASE WHEN uj.status = 'pending' THEN 1 ELSE 0 END) AS pending,
                    SUM(CASE WHEN uj.status = 'uploaded' THEN 1 ELSE 0 END) AS uploaded,
                    SUM(CASE WHEN uj.status = 'failed' THEN 1 ELSE 0 END) AS failed
                FROM schedule_batches sb
                JOIN creators c ON c.id = sb.creator_id
                LEFT JOIN upload_jobs uj ON uj.batch_id = sb.id
                WHERE sb.status = 'active'
                GROUP BY sb.id, c.display_name, c.username, sb.start_datetime,
                         sb.finish_datetime, sb.total_jobs
                ORDER BY sb.finish_datetime ASC
            """)

            results = []
            for row in cursor.fetchall():
                total = row["total_jobs"]
                results.append({
                    "batch_id": row["batch_id"],
                    "creator_name": row["creator_name"] or row["creator_username"],
                    "start_datetime": row["start_datetime"],
                    "finish_datetime": row["finish_datetime"],
                    "total_jobs": total,
                    "pending": row["pending"] or 0,
                    "uploaded": row["uploaded"] or 0,
                    "failed": row["failed"] or 0,
                })
        return results
    finally:
        conn.close()


# ==============================
# UPLOAD GAGAL
# ==============================

def get_failed_uploads():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    uj.id,
                    c.display_name AS creator_name,
                    c.username AS creator_username,
                    uj.product_id,
                    uj.schedule_datetime,
                    uj.retry_count,
                    uj.folder
                FROM upload_jobs uj
                JOIN creators c ON c.id = uj.creator_id
                WHERE uj.status = 'failed'
                ORDER BY uj.schedule_datetime DESC
            """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "creator_name": row["creator_name"] or row["creator_username"],
                    "product_id": row["product_id"],
                    "schedule_datetime": row["schedule_datetime"],
                    "retry_count": row["retry_count"],
                    "folder": row["folder"],
                })
        return results
    finally:
        conn.close()
