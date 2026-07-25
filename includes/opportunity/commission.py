# file : includes\opportunity\commission.py
"""
Opportunity Engine V5

Commission Score

Mengukur daya tarik komisi affiliate.

Komponen:
- Persentase komisi
- Nominal komisi
- Harga produk
"""

from .helpers import (
    clamp,
    make_score,
)


# ==========================================================
# CONFIG
# ==========================================================

IDEAL_PRICE = 45_000

MAX_PERCENT = 15

MAX_COMMISSION = 7_000


# ==========================================================
# MAIN
# ==========================================================

def calculate_commission_score(data):

    persen = max(
        float(data.get("persentase_komisi", 0)),
        0
    )

    komisi = max(
        float(data.get("komisi", 0)),
        0
    )

    price = max(
        float(data.get("price", 0)),
        0
    )

    # ======================================================
    # 1. Persentase Komisi
    # (paling penting)
    # ======================================================

    percent_score = clamp(
        (persen / MAX_PERCENT) * 100
    )

    # ======================================================
    # 2. Nominal Komisi
    # Rp7.000 dianggap maksimal
    # ======================================================

    nominal_score = clamp(

        (
            komisi /
            MAX_COMMISSION
        ) * 140

    )

    # ======================================================
    # 3. Harga Produk
    #
    # Ideal sekitar 45 ribu.
    # Semakin jauh dari 45 ribu,
    # score perlahan turun.
    # ======================================================

    if price <= 0:

        price_score = 50

    else:

        distance = abs(
            price - IDEAL_PRICE
        )

        price_score = clamp(
            100 -
            (
                distance /
                IDEAL_PRICE
            ) * 100
        )

    # ======================================================
    # FINAL
    #
    # Persentase paling penting.
    # ======================================================
    score = (

        percent_score * 0.60 +

        nominal_score * 0.25 +

        price_score * 0.15

    )
    # ======================================================

    if score >= 95:

        description = (
            "Komisi sangat menarik bagi affiliate."
        )

    elif score >= 85:

        description = (
            "Komisi berada di atas rata-rata."
        )

    elif score >= 75:

        description = (
            "Komisi cukup baik."
        )

    elif score >= 60:

        description = (
            "Komisi memenuhi batas minimum."
        )

    elif score >= 40:

        description = (
            "Komisi masih kurang menarik."
        )

    else:

        description = (
            "Komisi kurang layak untuk diprioritaskan."
        )

    return make_score(

        name="Commission",

        score=score,

        value={

            "persentase_komisi": persen,

            "komisi": komisi,

            "price": price,

            "percent_score": round(
                percent_score,
                2
            ),

            "nominal_score": round(
                nominal_score,
                2
            ),

            "price_score": round(
                price_score,
                2
            )

        },

        description=description

    )