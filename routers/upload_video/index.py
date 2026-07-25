from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    send_file
)
import os
import json
from datetime import datetime
from includes.product_lists_upload import open_product_lists
from includes.upload_manager import manager
from includes.valid_paths_project import valid_paths_project

upload_video_bp = Blueprint(
    "upload_video",
    __name__,
    url_prefix="/upload_video"
)


# ==========================================================
# Halaman Upload
# ==========================================================

@upload_video_bp.route("/", methods=["GET"])
def index():

    # Cari batch data dari upload_schedule.json di path_list terakhir yang diinput
    batch_data = None
    # Cek dari jobs yang sudah ada di manager
    if manager.jobs:
        parent_dir = os.path.dirname(manager.jobs[0])
        upload_schedule_path = os.path.join(parent_dir, "upload_schedule.json")
        if os.path.exists(upload_schedule_path):
            try:
                with open(upload_schedule_path, "r", encoding="utf-8") as f:
                    batch_data = json.load(f)
            except Exception:
                pass

    return render_template(
        "upload_video/index.html",
        batch_data=batch_data,
        manager_status=manager.status()
    )



# ==========================================================
# mendapatkan paths valid dari project video
# ==========================================================
@upload_video_bp.route("/get_paths", methods=["POST"])
def get_paths():

    file = request.files.get("file")

    if file is None:
        return jsonify({
            "success": False,
            "message": "File tidak ditemukan."
        }), 400

    try:

        paths = valid_paths_project(file)

    except Exception:

        return jsonify({
            "success": False,
            "message": "Format JSON tidak valid."
        }), 400

    return jsonify({
        "success": True,
        "paths": paths
    })


# ==========================================================
# Mulai Upload
# ==========================================================
@upload_video_bp.route("/start", methods=["POST"])
def proses_upload():

    source = request.form.get("source")
    path_list = request.form.get("path_list")
    json_file = request.files.get("json_file")

    result = manager.start({
        "source": source,
        "path_list": path_list,
        "json_file": json_file
    })

    return jsonify(result)


# ==========================================================
# Status Upload
# ==========================================================
@upload_video_bp.route("/status")
def status():
    return jsonify(manager.status())

# ==========================================================
# Stop Upload
# ==========================================================

@upload_video_bp.route("/stop", methods=["POST"])
def stop():

    manager.stop()

    return jsonify({
        "success": True
    })

@upload_video_bp.route("/product_lists", methods=["POST"])
def product_lists():

    paths = request.form.get("path_list")
    result = open_product_lists(paths)

    return render_template(
        "upload_video/product_lists.html",
        data=result
    )


# ==========================================================
# Product Image
# ==========================================================

@upload_video_bp.route("/product_image")
def product_image():

    path = request.args.get("path", "")

    if not path:
        return "", 404

    if not os.path.exists(path):
        return "", 404

    return send_file(path, mimetype="image/jpeg")
