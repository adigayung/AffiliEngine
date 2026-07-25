"""
Opportunity Engine V5

Trust Score

Mengukur tingkat kepercayaan produk.

Komponen:
- Rating
- Vote
- Sold
"""

from .helpers import (
    normalize_linear,
    normalize_log,
    make_score,
)


# ==========================================================
# CONFIG
# ==========================================================

MAX_RATING = 5.0

MAX_VOTE = 100_000

MAX_SOLD = 1_000_000


WEIGHT_RATING = 0.40
WEIGHT_VOTE = 0.30
WEIGHT_SOLD = 0.30


# ==========================================================
# MAIN
# ==========================================================

def calculate_trust_score(data):

    rating = max(
        float(data.get("rating", 0)),
        0
    )

    vote = max(
        float(data.get("vote", 0)),
        0
    )

    sold = max(
        float(data.get("sold", 0)),
        0
    )

    # ------------------------------------------------------

    rating_score = normalize_linear(
        rating,
        MAX_RATING
    )

    vote_score = normalize_log(
        vote,
        MAX_VOTE
    )

    sold_score = normalize_log(
        sold,
        MAX_SOLD
    )

    # ------------------------------------------------------

    final_score = (

        rating_score * WEIGHT_RATING +

        vote_score * WEIGHT_VOTE +

        sold_score * WEIGHT_SOLD

    )

    # ------------------------------------------------------

    if final_score >= 90:

        description = (
            "Produk memiliki tingkat kepercayaan yang sangat tinggi."
        )

    elif final_score >= 80:

        description = (
            "Produk memiliki reputasi yang baik."
        )

    elif final_score >= 70:

        description = (
            "Produk cukup terpercaya."
        )

    elif final_score >= 60:

        description = (
            "Tingkat kepercayaan produk sedang."
        )

    else:

        description = (
            "Produk belum memiliki reputasi yang kuat."
        )

    # ------------------------------------------------------

    return make_score(

        name="Trust",

        score=final_score,

        value={

            "rating": rating,

            "vote": int(vote),

            "sold": int(sold),

            "rating_score": round(
                rating_score,
                2
            ),

            "vote_score": round(
                vote_score,
                2
            ),

            "sold_score": round(
                sold_score,
                2
            ),

        },

        description=description

    )