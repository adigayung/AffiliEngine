# File : includes\opportunity\conversion.py
"""
Opportunity Engine V5

Conversion Score

Mengukur kemampuan produk menghasilkan penjualan.

Komponen:
- CTR
"""

from .helpers import (
    normalize_linear,
    make_score,
)


# ==========================================================
# CONFIG
# ==========================================================

# CTR (%) yang dianggap sangat bagus
MAX_CTR = 10


# ==========================================================
# MAIN
# ==========================================================

def calculate_conversion_score(data):

    ctr = max(
        float(data.get("ctr", 0)),
        0
    )

    ctr_score = normalize_linear(
        ctr,
        MAX_CTR
    )

    final_score = ctr_score

    # ======================================================

    if final_score >= 90:

        description = (
            "CTR sangat tinggi. Produk sangat menarik bagi calon pembeli."
        )

    elif final_score >= 80:

        description = (
            "CTR tinggi."
        )

    elif final_score >= 70:

        description = (
            "CTR cukup baik."
        )

    elif final_score >= 60:

        description = (
            "CTR berada di tingkat sedang."
        )

    else:

        description = (
            "CTR masih rendah."
        )

    # ======================================================

    return make_score(

        name="Conversion",

        score=final_score,

        value={

            "ctr": ctr,

            "ctr_score": round(
                ctr_score,
                2
            )

        },

        description=description

    )