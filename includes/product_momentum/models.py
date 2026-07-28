"""
Product Momentum - Data Models.

Menyimpan struktur data yang digunakan oleh analyzer.
Menggunakan namedtuple untuk data yang immutable dan simple,
dan kelas biasa untuk yang membutuhkan lebih banyak logika.
"""

from collections import namedtuple
from typing import List, Dict, Any, Optional


# ================================================================
# Named Tuples
# ================================================================

ProductSummary = namedtuple("ProductSummary", [
    "total_products",
    "products_analyzed",
    "total_creators",
    "total_videos",
    "avg_momentum",
    "highest_momentum",
    "highest_momentum_product",
])

ChartData = namedtuple("ChartData", [
    "momentum",
    "discovery",
    "distribution",
    "category",
])


def empty_chart_data():
    """Mengembalikan ChartData kosong untuk empty state."""
    return ChartData(
        momentum={"labels": [], "data": [], "colors": []},
        discovery={"labels": [], "data": [], "colors": []},
        distribution={"labels": [], "data": [], "colors": []},
        category={"labels": [], "data": [], "colors": {}},
    )
