"""
Opportunity Engine V5

Product Quality

Mengukur kualitas produk berdasarkan rating produk
(skala 0.0 - 5.0).
"""

from .helpers import (
    normalize_linear,
    make_score,
)


# ==========================================================
# CONFIG
# ==========================================================

MAX_RATING = 5.0


# ==========================================================
# MAIN
# ==========================================================

def calculate_product_quality_score(data):

    rating = max(
        float(data.get("rating", 0) or 0),
        0
    )

    # Rating (0.0 - 5.0) dinormalisasi ke skala 0 - 100 HANYA untuk
    # keperluan internal (bobot opportunity score & progress bar).
    # Angka yang ditampilkan ke user tetap rating asli 0.0 - 5.0.
    rating_score = normalize_linear(
        rating,
        MAX_RATING
    )

    final_score = rating_score

    # ======================================================

    if rating >= 4.5:

        description = (
            "Rating produk sangat tinggi, mayoritas pembeli sangat puas."
        )

    elif rating >= 4.0:

        description = (
            "Rating produk tinggi, pembeli umumnya puas."
        )

    elif rating >= 3.0:

        description = (
            "Rating produk cukup baik."
        )

    elif rating >= 2.0:

        description = (
            "Rating produk tergolong sedang."
        )

    elif rating > 0:

        description = (
            "Rating produk rendah, banyak ulasan negatif."
        )

    else:

        description = (
            "Produk belum memiliki rating."
        )

    # ======================================================

    return make_score(

        name="Product Quality",

        score=final_score,

        value={

            "rating": rating,

            "rating_max": MAX_RATING,

            "rating_percent": round(
                rating_score,
                2
            )

        },

        description=description

    )