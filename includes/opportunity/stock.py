"""
Opportunity Engine V5

Stock Score

Mengukur kesiapan stok produk.

Semakin banyak stok tersedia,
semakin kecil kemungkinan kehilangan penjualan.
"""

from .helpers import (
    normalize_log,
    make_score,
)


# ==========================================================
# CONFIG
# ==========================================================

MAX_STOCK = 100_000


# ==========================================================
# MAIN
# ==========================================================

def calculate_stock_score(data):

    stok = max(
        float(data.get("stok_tersedia", 0)),
        0
    )

    stock_score = normalize_log(
        stok,
        MAX_STOCK
    )

    # ======================================================

    if stock_score >= 90:

        description = (
            "Stok produk sangat melimpah."
        )

    elif stock_score >= 80:

        description = (
            "Stok produk sangat aman."
        )

    elif stock_score >= 70:

        description = (
            "Stok produk cukup tersedia."
        )

    elif stock_score >= 60:

        description = (
            "Stok produk mulai terbatas."
        )

    else:

        description = (
            "Stok produk rendah."
        )

    # ======================================================

    return make_score(

        name="Stock",

        score=stock_score,

        value={

            "stok_tersedia": int(stok),

            "stock_score": round(
                stock_score,
                2
            )

        },

        description=description

    )