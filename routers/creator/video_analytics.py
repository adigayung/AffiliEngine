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
from includes.mysql import match_tiktok_videos_to_jobs

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
    max_videos = 60
    result = update_creator_analytics(creator_id, max_videos)

    # Lakukan video-job matching hanya jika update analytics berhasil
    if result.get("success"):
        matched_count = match_tiktok_videos_to_jobs()
        result["matched"] = matched_count

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
    # HITUNG SUMMARY GROWTH
    # ==============================
    videos = data.get("videos", [])
    total_video = data.get("total_video", 0)
    stats = data.get("statistics", {})

    # Growth = sum of per-video growth values
    total_views_growth = sum(v.get("views_growth", 0) or 0 for v in videos)
    total_likes_growth = sum(v.get("likes_growth", 0) or 0 for v in videos)
    total_comments_growth = sum(v.get("comments_growth", 0) or 0 for v in videos)
    total_shares_growth = sum(v.get("shares_growth", 0) or 0 for v in videos)
    total_favorites_growth = sum(v.get("favorites_growth", 0) or 0 for v in videos)

    # Hitung avg, median, highest, lowest views
    all_views = sorted([v.get("views", 0) or 0 for v in videos])
    total_views = stats.get("total_views", 0)
    total_favorites = stats.get("total_favorites", 0)

    avg_views = total_views // total_video if total_video > 0 else 0
    highest_views = all_views[-1] if all_views else 0
    lowest_views = all_views[0] if all_views else 0

    median_views = 0
    if all_views:
        n = len(all_views)
        if n % 2 == 0:
            median_views = (all_views[n // 2 - 1] + all_views[n // 2]) // 2
        else:
            median_views = all_views[n // 2]

    # Growth untuk derived stats = 0 (tidak ada history)
    avg_views_growth = 0
    median_views_growth = 0
    highest_views_growth = 0
    lowest_views_growth = 0
    total_video_growth = 0

    # Tambahkan ke data untuk template
    data["total_video_growth"] = total_video_growth
    data["total_views_growth"] = total_views_growth
    data["avg_views_growth"] = avg_views_growth
    data["median_views_growth"] = median_views_growth
    data["highest_views_growth"] = highest_views_growth
    data["lowest_views_growth"] = lowest_views_growth
    data["total_likes_growth"] = total_likes_growth
    data["total_comments_growth"] = total_comments_growth
    data["total_shares_growth"] = total_shares_growth
    data["total_favorites_growth"] = total_favorites_growth

    data["avg_views"] = avg_views
    data["median_views"] = median_views
    data["highest_views"] = highest_views
    data["lowest_views"] = lowest_views

    # ==============================
    # RISING VIDEOS — Top 7 pertumbuhan tercepat
    # ==============================
    rising_videos = video_analytics_service.get_rising_videos(creator_id)
    data["rising_videos"] = rising_videos

    # ==============================
    # RENDER TEMPLATE
    # ==============================
    return render_template(
        "video_analytics/index.html",
        page_title=f"Video Analytics - {display_name}",
        **data
    )
