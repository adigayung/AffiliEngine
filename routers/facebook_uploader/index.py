"""
routers/facebook_uploader/index.py — Router Facebook Uploader.

Mengikuti pola routers/upload_video/index.py (TikTok uploader).
Router hanya melakukan orkestrasi:
  - render halaman
  - membaca/menyiapkan data (upload_schedule.json)
  - validasi project path (READ-ONLY)
  - menjalankan FacebookUploader melalui background manager
  - mengirim status/result ke template

Seluruh logic Selenium tetap berada di package includes/facebook_uploader/.
"""

from flask import Blueprint, render_template, request, jsonify

from includes.facebook_paths import validate_facebook_batch
from includes.facebook_upload_manager import facebook_manager

facebook_uploader_bp = Blueprint(
    "facebook_uploader",
    __name__,
    url_prefix="/upload_video/facebook",
)


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

    # Simpan log validasi ke manager agar tetap tampil saat status di-poll.
    facebook_manager.set_validation_logs(result["details"])

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
    path_list = request.form.get("path_list", "")
    result = facebook_manager.start(path_list)
    return jsonify(result)


# ==========================================================
# Status Upload
# ==========================================================

@facebook_uploader_bp.route("/status", methods=["GET"])
def status():
    return jsonify(facebook_manager.status())


# ==========================================================
# Stop Upload
# ==========================================================

@facebook_uploader_bp.route("/stop", methods=["POST"])
def stop():
    result = facebook_manager.stop()
    return jsonify(result)
