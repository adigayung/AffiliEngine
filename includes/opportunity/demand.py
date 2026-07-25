# File : includes\opportunity\demand.py
"""
Opportunity Engine V5

Demand Score

Mengukur seberapa besar permintaan produk.

Komponen:
- Pesanan
- Pembeli Keranjang
"""

from .helpers import (
    normalize_log,
    make_score,
)


# ==========================================================
# CONFIG
# ==========================================================

MAX_PESANAN = 10_000

MAX_KERANJANG = 20_000

WEIGHT_PESANAN = 0.65

WEIGHT_KERANJANG = 0.35


# ==========================================================
# MAIN
# ==========================================================

def calculate_demand_score(data):

    pesanan = max(
        float(data.get("pesanan", 0)),
        0
    )

    keranjang = max(
        float(data.get("pembeli_keranjang", 0)),
        0
    )

    pesanan_score = normalize_log(
        pesanan,
        MAX_PESANAN
    )

    keranjang_score = normalize_log(
        keranjang,
        MAX_KERANJANG
    )

    final_score = (

        pesanan_score * WEIGHT_PESANAN +

        keranjang_score * WEIGHT_KERANJANG

    )

    # ======================================================

    if final_score >= 90:

        description = (
            "Permintaan produk sangat tinggi."
        )

    elif final_score >= 80:

        description = (
            "Permintaan produk tinggi."
        )

    elif final_score >= 70:

        description = (
            "Permintaan produk cukup baik."
        )

    elif final_score >= 60:

        description = (
            "Permintaan produk sedang."
        )

    else:

        description = (
            "Permintaan produk masih rendah."
        )

    # ======================================================

    return make_score(

        name="Demand",

        score=final_score,

        value={

            "pesanan": int(pesanan),

            "keranjang": int(keranjang),

            "pesanan_score": round(
                pesanan_score,
                2
            ),

            "keranjang_score": round(
                keranjang_score,
                2
            )

        },

        description=description
    )