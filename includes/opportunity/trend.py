# File : includes\opportunity\trend.py
"""
Opportunity Engine V5

Trend Score

Mengukur trend produk berdasarkan
rasio Pembeli Keranjang terhadap Pesanan.

Semakin tinggi rasio keranjang,
semakin besar potensi pertumbuhan produk.
"""

from .helpers import (
    normalize_linear,
    sigmoid,
    make_score,
)


# ==========================================================
# CONFIG
# ==========================================================

# Rasio keranjang/pesanan yang dianggap sangat bagus.
# Contoh:
# 1000 pesanan
# 1000 keranjang
# ratio = 1.0 (100%)

MAX_RATIO = 1.0


# ==========================================================
# MAIN
# ==========================================================

def calculate_trend_score(data):

    pesanan = max(
        float(data.get("pesanan", 0)),
        1
    )

    keranjang = max(
        float(data.get("pembeli_keranjang", 0)),
        0
    )

    ratio = keranjang / pesanan

    # trend_score = normalize_linear(
    #     ratio,
    #     MAX_RATIO
    # )
    trend_score = sigmoid(
        ratio,
        midpoint=2,
        steepness=1.2
    )
    # ======================================================

    if trend_score >= 90:

        description = (
            "Trend produk sangat kuat dan masih bertumbuh."
        )

    elif trend_score >= 80:

        description = (
            "Trend produk masih sangat baik."
        )

    elif trend_score >= 70:

        description = (
            "Trend produk cukup baik."
        )

    elif trend_score >= 60:

        description = (
            "Trend produk berada di tingkat sedang."
        )

    else:

        description = (
            "Trend produk mulai melemah."
        )

    # ======================================================

    return make_score(

        name="Trend",

        score=trend_score,

        value={

            "pesanan": int(pesanan),

            "keranjang": int(keranjang),

            "cart_ratio": round(
                ratio,
                4
            ),

            "trend_score": round(
                trend_score,
                2
            )

        },

        description=description

    )