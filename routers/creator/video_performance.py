"""Video Performance Router.

Route: /creator/<creator_id>/video_performance
"""

from flask import Blueprint, render_template, request, jsonify, abort
from includes.mysql import get_creator, get_video_performance_summary, get_video_performance_list
from includes.video_performance import manager

video_performance_bp = Blueprint(
    "video_performance",
    __name__,
    url_prefix="/creator"
)

@video_performance_bp.route("/<int:creator_id>/video_performance")
def video_performance(creator_id):
    """
    Halaman Video Performance untuk satu Creator.
    Data dibaca dari database, TIDAK melakukan scan.
    """
    creator = get_creator(creator_id)
    if not creator:
        abort(404, description="Creator tidak ditemukan")

    # Ambil summary dan list dari database
    summary = get_video_performance_summary(creator_id)
    videos = get_video_performance_list(creator_id)

    return render_template(
        "creator/video_performance.html",
        page_title="Video Performance - " + (creator.get("display_name") or creator.get("username", "Unknown")),
        creator=creator,
        summary=summary,
        videos=videos,
    )


@video_performance_bp.route("/<int:creator_id>/video_performance/scan", methods=["POST"])
def video_performance_scan(creator_id):
    """
    Mulai scan untuk creator.
    Background job - mengikuti pattern UploadManager.
    """
    creator = get_creator(creator_id)
    if not creator:
        return jsonify({"success": False, "message": "Creator tidak ditemukan"}), 404

    result = manager.start(creator_id)
    return jsonify(result)


@video_performance_bp.route("/<int:creator_id>/video_performance/status")
def video_performance_status(creator_id):
    """
    Polling status scan.
    """
    status = manager.status()
    return jsonify(status)


@video_performance_bp.route("/<int:creator_id>/video_performance/stop", methods=["POST"])
def video_performance_stop(creator_id):
    """
    Hentikan scan.
    """
    result = manager.stop()
    return jsonify(result)

