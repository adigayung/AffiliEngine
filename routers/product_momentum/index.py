"""
Product Momentum Router.

Route: /product_momentum
"""

from flask import Blueprint, render_template, jsonify
from includes.product_momentum import analyze_product_momentum

product_momentum_bp = Blueprint(
    "product_momentum",
    __name__,
    url_prefix="/product_momentum",
)


@product_momentum_bp.route("/")
def index():
    """
    Halaman utama Product Momentum.
    Menampilkan dashboard analisis momentum produk.
    """
    try:
        results = analyze_product_momentum()
    except Exception as e:
        # Jika ada error (misal database kosong), return empty state
        results = {
            "summary": {
                "total_products": 0,
                "products_analyzed": 0,
                "total_creators": 0,
                "total_videos": 0,
                "avg_momentum": 0,
                "highest_momentum": 0,
                "highest_momentum_product": "",
            },
            "momentum_rank": [],
            "discovery_rank": [],
            "all_results": [],
            "chart_data": {
                "momentum": {"labels": [], "data": [], "colors": []},
                "discovery": {"labels": [], "data": [], "colors": []},
                "distribution": {"labels": [], "data": [], "colors": []},
                "category": {"labels": [], "data": [], "colors": {}},
            },
            "total_products": 0,
            "error": str(e),
        }

    return render_template(
        "product_momentum/index.html",
        page_title="Product Momentum",
        summary=results.get("summary", {}),
        momentum_rank=results.get("momentum_rank", [])[:10],
        discovery_rank=results.get("discovery_rank", [])[:10],
        all_results=results.get("all_results", [])[:10],
        chart_data=results.get("chart_data", {}),
        total_products=results.get("total_products", 0),
        has_data=len(results.get("all_results", [])) > 0,
    )


@product_momentum_bp.route("/api/data")
def api_data():
    """
    API endpoint untuk mendapatkan data Product Momentum dalam format JSON.
    Berguna untuk debugging atau integrasi dengan komponen frontend.
    """
    try:
        results = analyze_product_momentum()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e), "data": []}), 500
