"""
Video Analytics Router (Thin Controller).

Route: /creator/<creator_id>/video_analytics

Router hanya bertugas:
    1. Menerima parameter creator_id
    2. Memanggil Service Layer (includes.video_analytics.video_analytics)
    3. Menerima object hasil
    4. Melakukan render_template()

Router TIDAK boleh:
    - Melakukan query database
    - Memproses data
    - Mengetahui struktur data Video Analytics
    - Mengetahui bagaimana workflow Video Analytics bekerja
    - Memiliki business logic
"""

from flask import Blueprint, render_template, abort, jsonify, request
from includes.video_analytics.video_analytics import video_analytics_service, update_creator_analytics

creator_video_analytics_bp = Blueprint(
    "creator_video_analytics",
    __name__,
    url_prefix="/creator"
)


@creator_video_analytics_bp.route("/<int:creator_id>/video_analytics/update", methods=["POST"])
def video_analytics_update(creator_id):
    """
    Update Analytics untuk satu Creator.
    URL: POST /creator/<creator_id>/video_analytics/update

    Router hanya sebagai coordinator. Business logic ada di
    includes.video_analytics.video_analytics.update_creator_analytics()
    """
    max_videos = 30
    result = update_creator_analytics(creator_id, max_videos)
    return jsonify(result)


@creator_video_analytics_bp.route("/<int:creator_id>/video_analytics")
def video_analytics(creator_id):
    """
    Halaman Video Analytics untuk satu Creator.
    URL: /creator/<creator_id>/video_analytics
    """
    # ==============================
    # PANGGIL SERVICE LAYER
    # ==============================
    data = video_analytics_service.index(creator_id)

    # ==============================
    # HANDLE CREATOR NOT FOUND
    # ==============================
    if data is None:
        abort(404, description="Creator tidak ditemukan")

    creator = data["creator"]
    display_name = creator.get("display_name") or creator.get("username", "Unknown")

    # ==============================
    # RENDER TEMPLATE
    # ==============================
    return render_template(
        "video_analytics/index.html",
        page_title=f"Video Analytics - {display_name}",
        **data
    )
