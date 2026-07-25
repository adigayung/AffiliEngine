"""
Opportunity Engine V5

Price Score

Mengukur daya tarik harga produk
untuk TikTok Affiliate.

Semakin dekat dengan sweet spot,
semakin tinggi score.
"""

from .helpers import make_score


# ==========================================================
# MAIN
# ==========================================================

def calculate_price_score(data):

    price = max(
        float(data.get("price", 0)),
        0
    )

    # ======================================================
    # Sweet Spot Price (Rupiah)
    # ======================================================

    if price <= 0:

        score = 0

    elif price < 20_000:

        score = 70

    elif price < 80_000:

        score = 100

    elif price < 150_000:

        score = 95

    elif price < 300_000:

        score = 80

    elif price < 500_000:

        score = 60

    elif price < 1_000_000:

        score = 40

    else:

        score = 20

    # ======================================================

    if score >= 95:

        description = (
            "Harga berada pada rentang ideal untuk impulse buying."
        )

    elif score >= 80:

        description = (
            "Harga masih sangat menarik untuk pasar affiliate."
        )

    elif score >= 60:

        description = (
            "Harga masih cukup kompetitif."
        )

    elif score >= 40:

        description = (
            "Harga mulai membatasi potensi konversi."
        )

    elif score > 0:

        description = (
            "Harga relatif tinggi untuk pasar affiliate."
        )

    else:

        description = (
            "Harga produk tidak tersedia."
        )

    # ======================================================

    return make_score(

        name="Price",

        score=score,

        value={

            "price": int(price)

        },

        description=description

    )