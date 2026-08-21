"""
routers/facebook_uploader/index.py — Router Facebook Uploader.

Mengikuti pola routers/upload_video/index.py (TikTok uploader).
Router hanya melakukan orkestrasi:
  - render halaman
  - membaca/menyiapkan data (upload_schedule.json)
  - validasi project path (READ-ONLY)
  - menjalankan uploader melalui background manager
  - mengirim status/result ke template

Phase 4 — DUA METODE UPLOAD:
  - method="pc" (DEFAULT, behavior lama TIDAK berubah):
        facebook_manager (Selenium PC) — facebook_uploader package existing.
  - method="hp":
        facebook_hp_manager + WebSocket Android (Phase 1-3).
        Job diproses oleh konsumen WebSocket /service/video_uploader.

Seluruh logic Selenium tetap berada di package includes/facebook_uploader/,
dan seluruh logic Facebook HP tetap di includes/facebook_hp_manager.py /
includes/jobs/workflows_facebook.py / includes/jobs/facebook_job_runner.py.
"""

from flask import Blueprint, render_template, request, jsonify

from includes.facebook_paths import validate_facebook_batch
from includes.facebook_upload_manager import facebook_manager
from includes.facebook_hp_manager import facebook_hp_manager
from includes.android.device_connection import device_connection

facebook_uploader_bp = Blueprint(
    "facebook_uploader",
    __name__,
    url_prefix="/upload_video/facebook",
)

# Mode upload aktif. DEFAULT = "pc" agar behavior lama tetap sama.
# Di-set saat /start sukses; dipakai /status & /stop bila UI tidak
# mengirim parameter method eksplisit.
_fb_active_method = "pc"


def _normalize_method(method):
    """Normalisasi method ke 'pc' / 'hp'; default 'pc' (behavior lama)."""
    method = str(method or "").strip().lower()
    return method if method in ("pc", "hp") else "pc"


# ==========================================================
# Halaman Facebook Uploader
# ==========================================================

@facebook_uploader_bp.route("/", methods=["GET"])
def index():
    return render_template("upload_video/facebook_uploader.html")


# ==========================================================
# Mendapatkan paths valid dari upload_schedule.json
# ==========================================================

@facebook_uploader_bp.route("/get_paths", methods=["POST"])
def get_paths():
    file = request.files.get("file")

    if file is None:
        return jsonify({
            "success": False,
            "message": "File tidak ditemukan."
        }), 400

    try:
        result = validate_facebook_batch(file)
    except Exception:
        return jsonify({
            "success": False,
            "message": "Format JSON tidak valid."
        }), 400

    # Simpan log validasi ke KEDUA manager (PC & HP) agar tetap tampil
    # saat status di-poll, apapun metode upload yang dipilih.
    facebook_manager.set_validation_logs(result["details"])
    facebook_hp_manager.set_validation_logs(result["details"])

    return jsonify({
        "success": True,
        "paths": result["paths"],
        "summary": result["summary"],
        "logs": result["details"],
    })


# ==========================================================
# Mulai Upload (background execution)
# ==========================================================

@facebook_uploader_bp.route("/start", methods=["POST"])
def start():
    global _fb_active_method

    path_list = request.form.get("path_list", "")
    method = _normalize_method(request.form.get("method"))

    if method == "hp":
        # Guard isolasi: jangan jalankan Via HP bersamaan dengan Via PC.
        if facebook_manager.running:
            return jsonify({
                "success": False,
                "message": "Upload Via PC masih berjalan. Tekan STOP terlebih dahulu.",
                "code": "already_running",
            })

        # facebook_hp_manager: queue disiapkan, JOB diproses oleh konsumen
        # WebSocket Android (Phase 1-3). Tidak spawn thread worker.
        result = facebook_hp_manager.start(path_list)
        if result.get("success"):
            _fb_active_method = "hp"
        return jsonify(result)

    # method == "pc" — Selenium flow existing TIDAK berubah.
    if facebook_hp_manager.running:
        return jsonify({
            "success": False,
            "message": "Queue Via HP masih berjalan. Tekan STOP terlebih dahulu.",
            "code": "already_running",
        })

    result = facebook_manager.start(path_list)
    if result.get("success"):
        _fb_active_method = "pc"
    return jsonify(result)


# ==========================================================
# Status Upload
# ==========================================================

@facebook_uploader_bp.route("/status", methods=["GET"])
def status():
    # UI mengirim method eksplisit (?method=pc|hp); fallback ke mode aktif.
    method = _normalize_method(request.args.get("method", _fb_active_method))

    if method == "hp":
        data = facebook_hp_manager.status()
        data["method"] = "hp"
        data["android_connected"] = device_connection.is_connected()
        data["android"] = device_connection.status()
        return jsonify(data)

    data = facebook_manager.status()
    data["method"] = "pc"
    return jsonify(data)


# ==========================================================
# Stop Upload
# ==========================================================

@facebook_uploader_bp.route("/stop", methods=["POST"])
def stop():
    # UI mengirim method; fallback ke mode aktif (default pc = behavior lama).
    method = _normalize_method(request.form.get("method", _fb_active_method))

    if method == "hp":
        result = facebook_hp_manager.stop()
        result["method"] = "hp"
        return jsonify(result)

    result = facebook_manager.stop()
    result["method"] = "pc"
    return jsonify(result)
