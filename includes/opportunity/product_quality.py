"""
Opportunity Engine V5

Product Quality

Mengukur kualitas produk berdasarkan
persentase ulasan positif.
"""

from .helpers import (
    normalize_linear,
    make_score,
)


# ==========================================================
# MAIN
# ==========================================================

def calculate_product_quality_score(data):

    ulasan = max(
        float(data.get("ulasan_positif", 0)),
        0
    )

    review_score = normalize_linear(
        ulasan,
        100
    )

    final_score = review_score

    # ======================================================

    if final_score >= 95:

        description = (
            "Mayoritas pembeli memberikan ulasan yang sangat positif."
        )

    elif final_score >= 90:

        description = (
            "Ulasan produk sangat baik."
        )

    elif final_score >= 80:

        description = (
            "Ulasan produk cukup baik."
        )

    elif final_score >= 70:

        description = (
            "Kualitas produk tergolong sedang."
        )

    else:

        description = (
            "Banyak ulasan negatif atau data ulasan masih rendah."
        )

    # ======================================================

    return make_score(

        name="Product Quality",

        score=final_score,

        value={

            "ulasan_positif": ulasan,

            "review_score": round(
                review_score,
                2
            )

        },

        description=description

    )