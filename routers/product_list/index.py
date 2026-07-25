# File : routers\product_list\index.py
import json
from flask import Blueprint, render_template, request, jsonify, session
from includes.product_list  import get_product_list
from includes.prepare_upload  import generate_prepare_upload
from includes.compare_products import bandingkan, apply_weight_ai
from includes.upload_scheduler import create_upload_schedule
from includes.mysql import get_creator
from includes.logFX import logger
from includes.schedule.scheduler import UploadScheduler
from includes.mysql import remove_product
from includes.schedule.import_analyzer import analyze_upload_schedule, analyze_upload_schedule_from_data
from includes.mysql import get_creator_list

product_list_bp = Blueprint(
    "product_list",
    __name__,
    url_prefix="/product_list"
)

@product_list_bp.route("/")
def index():

    products = get_product_list()
    #logger("debug", f"isi : {products}")
    
    return render_template(
        "product_list/index.html",
        products=products
    )

@product_list_bp.route(
    "/remove/<int:product_id>",
    methods=["POST"]
)
def remove_prodak(product_id):

    print("product_id : ", product_id)
    remove_product(product_id)

    return {
        "success": True
    }

@product_list_bp.route(
    "/prepare_upload/apply_weight",
    methods=["POST"]
)
def apply_weight():

    total_video = int(
        request.form.get(
            "total_video",
            0
        )
    )

    ai_result = json.loads(
        request.form.get(
            "ai_result",
            "{}"
        )
    )

    hasil = apply_weight_ai(
        ai_result,
        total_video
    )

    return jsonify(hasil)

@product_list_bp.route("/prepare_upload/compare_products", methods=["POST"])
def compare_products():

    products = json.loads(
        request.form.get("products", "[]")
    )

    # try:

    hasil = bandingkan(products)
    #print(hasil)
    return jsonify(hasil)

    # except Exception as e:

    #     return jsonify({

    #         "success": False,

    #         "message": str(e)

    #     }), 500
    
@product_list_bp.route("/prepare_upload/videos", methods=["POST"])
def prepare_upload():

    products = json.loads(request.form.get("products", "[]"))
    hasil = generate_prepare_upload(products)

    #print(produk_input)
    return render_template(
        "product_list/prepare_upload_videos.html",
        products=hasil
    )

@product_list_bp.route("/prepare_upload/jadwal", methods=["POST"])
def prepare_jadwal():

    products = json.loads(request.form.get("products", "{}"))

    #print(products)
    return render_template(
        "product_list/prepare_jadwal.html",
        products=products
    )


@product_list_bp.route(
    "/prepare_upload/import_analyze",
    methods=["POST"]
)
def import_analyze():
    """
    Menganalisis pola jadwal dari data JSON yang diupload user.
    """
    json_str = request.form.get("json_data", "")

    if not json_str:
        return jsonify({
            "success": False,
            "error": "Tidak ada data JSON."
        })

    try:
        data = json.loads(json_str)
        result = analyze_upload_schedule_from_data(data)
        return jsonify(result)

    except json.JSONDecodeError as e:
        return jsonify({
            "success": False,
            "error": f"JSON tidak valid: {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error: {str(e)}"
        })

@product_list_bp.route("/prepare_upload/check_creator", methods=["GET"])
def check_creator():
    """
    Mengecek apakah creator sudah dipilih di session.
    Digunakan oleh frontend sebelum submit form.
    """
    creator_id = session.get("creator_id")
    if creator_id:
        creator = get_creator(creator_id)
        if creator:
            return jsonify({
                "success": True,
                "creator": {
                    "id": creator["id"],
                    "display_name": creator["display_name"],
                    "username": creator["username"]
                }
            })

    # Creator belum dipilih, kirim daftar creator untuk modal
    creators = get_creator_list()
    return jsonify({
        "success": False,
        "require_creator": True,
        "message": "Please select creator first.",
        "creators": [
            {
                "id": c["id"],
                "display_name": c["display_name"],
                "username": c["username"],
                "profile_image": c.get("profile_image", "")
            }
            for c in creators
        ]
    })


@product_list_bp.route("/prepare_upload/buat_jadwal", methods=["POST"])
def buat_jadwal():
    # ==============================
    # VALIDASI CREATOR
    # ==============================
    creator_id = session.get("creator_id")
    if not creator_id:
        return jsonify({
            "success": False,
            "require_creator": True,
            "message": "Please select creator first."
        }), 200  # 200 bukan 500, agar tidak trigger error handler

    current_creator = get_creator(creator_id)
    if not current_creator:
        return jsonify({
            "success": False,
            "require_creator": True,
            "message": "Selected creator not found. Please select again."
        }), 200

    schedule_mode = request.form.get("schedule_mode")

    scheduler = UploadScheduler(request)

    if schedule_mode == "interval":

        result = scheduler.interval()

    elif schedule_mode == "fixed":

        result = scheduler.fixed_time()

    elif schedule_mode == "weekly":

        weekly_schedule = json.loads(
            request.form.get("weekly_schedule", "{}")
        )

        result = scheduler.weekly(
            weekly_schedule
        )

    elif schedule_mode == "pattern":

        result = scheduler.pattern()

    elif schedule_mode == "import_schedule":

        result = scheduler.import_schedule()

    else:

        return {
            "status": False,
            "message": "Invalid schedule mode."
        }

    return render_template(

        "product_list/buat_jadwal.html",

        **result

    )

