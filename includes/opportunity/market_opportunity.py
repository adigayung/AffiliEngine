"""
Opportunity Engine V5

Market Opportunity

Mengukur peluang pasar berdasarkan
Demand per Creator.

Semakin tinggi jumlah pesanan
dibanding jumlah kreator,
semakin besar peluang market.
"""

from .helpers import (
    normalize_log,
    make_score,
)


# ==========================================================
# CONFIG
# ==========================================================

MAX_RATIO = 100


# ==========================================================
# MAIN
# ==========================================================

def calculate_market_opportunity_score(data):

    pesanan = max(
        float(data.get("pesanan", 0)),
        0
    )

    kreator = max(
        float(data.get("jumlah_kreator", 1)),
        1
    )

    ratio = pesanan / kreator

    market_score = normalize_log(
        ratio,
        MAX_RATIO
    )

    # ======================================================

    if market_score >= 90:

        description = (
            "Peluang market sangat besar."
        )

    elif market_score >= 80:

        description = (
            "Peluang market masih sangat baik."
        )

    elif market_score >= 70:

        description = (
            "Peluang market cukup baik."
        )

    elif market_score >= 60:

        description = (
            "Peluang market berada di tingkat sedang."
        )

    else:

        description = (
            "Persaingan market relatif tinggi."
        )

    # ======================================================

    return make_score(

        name="Market Opportunity",

        score=market_score,

        value={

            "pesanan": int(pesanan),

            "jumlah_kreator": int(kreator),

            "demand_per_creator": round(
                ratio,
                2
            ),

            "market_score": round(
                market_score,
                2
            )

        },

        description=description

    )