# File: routers/production_monitor/index.py
# Router untuk modul Monitor Produksi (hanya memanggil function dari includes)

from flask import Blueprint, render_template
from includes.production_monitor import (
    get_summary,
    get_fokus_hari_ini,
    get_tugas_hari_ini,
    get_creator_status,
    get_active_batches,
    get_failed_uploads,
)

production_monitor_bp = Blueprint(
    "production_monitor",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/production_monitor/static",
)


@production_monitor_bp.route("/production_monitor/")
def index():
    """
    Halaman utama Monitor Produksi.
    Menampilkan Production Planner harian.
    """
    summary = get_summary()
    fokus = get_fokus_hari_ini()
    tugas_data = get_tugas_hari_ini()
    all_creators = get_creator_status()
    active_batches = get_active_batches()
    failed_uploads = get_failed_uploads()

    return render_template(
        "production_monitor/index.html",
        page_title="Monitor Produksi",
        summary=summary,
        fokus=fokus,
        tugas_list=tugas_data["tugas"],
        tugas_ada_lebih=tugas_data["ada_lebih"],
        tugas_total_semua=tugas_data["total_semua"],
        all_creators=all_creators,
        active_batches=active_batches,
        failed_uploads=failed_uploads,
    )
