# FILE : includes\opportunity\competition.py
"""
Opportunity Engine V5

Competition Score

Mengukur tingkat persaingan affiliate.

Semakin sedikit jumlah kreator,
semakin tinggi score.
"""

from .helpers import (
    normalize_inverse,
    normalize_inverse_log,
    make_score,
)


# ==========================================================
# CONFIG
# ==========================================================

MAX_CREATOR = 51_000


# ==========================================================
# MAIN
# ==========================================================

def calculate_competition_score(data):

    kreator = max(
        float(data.get("jumlah_kreator", 0)),
        0
    )

    competition_score = normalize_inverse_log(
        kreator,
        MAX_CREATOR
    )

    # ======================================================
    print("=" *70)
    print ("data ",  data)
    if competition_score >= 90:

        description = (
            "Persaingan affiliate masih sangat rendah."
        )

    elif competition_score >= 80:

        description = (
            "Persaingan affiliate masih rendah."
        )

    elif competition_score >= 70:

        description = (
            "Persaingan affiliate cukup sehat."
        )

    elif competition_score >= 60:

        description = (
            "Persaingan affiliate mulai meningkat."
        )

    else:

        description = (
            "Persaingan affiliate cukup tinggi."
        )

    # ======================================================

    return make_score(

        name="Competition",

        score=competition_score,

        value={

            "jumlah_kreator": int(kreator),

            "competition_score": round(
                competition_score,
                2
            )

        },

        description=description

    )