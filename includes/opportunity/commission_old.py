"""
Opportunity Engine V5

Commission Score

Mengukur daya tarik komisi affiliate.
"""

from .helpers import make_score


# ==========================================================
# MAIN
# ==========================================================

def calculate_commission_score(data):

    komisi = max(
        float(data.get("komisi", 0)),
        0
    )

    # ======================================================
    # Commission Curve
    #
    # <6%  : Tidak Layak
    # 6-7  : Minimal
    # 7-8  : Cukup
    # 8-9  : Baik
    # 9-10 : Sangat Baik
    # 10-12: Excellent
    # >=12 : Maksimal
    # ======================================================

    if komisi < 6:

        score = 0

    elif komisi < 7:

        score = 40

    elif komisi < 8:

        score = 60

    elif komisi < 9:

        score = 75

    elif komisi < 10:

        score = 85

    elif komisi < 12:

        score = 95

    else:

        score = 100

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

    elif score > 0:

        description = (
            "Komisi masih rendah."
        )

    else:

        description = (
            "Komisi di bawah 6% dan tidak direkomendasikan."
        )

    return make_score(

        name="Commission",

        score=score,

        value={
            "komisi": komisi
        },

        description=description

    )
