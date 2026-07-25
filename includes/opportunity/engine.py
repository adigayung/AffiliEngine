"""
Opportunity Engine V5

Core Engine
"""

from .weights import WEIGHTS

from .rating import get_rating

from .explain import generate_summary

from .demand import calculate_demand_score
from .conversion import calculate_conversion_score
from .product_quality import calculate_product_quality_score
from .trust import calculate_trust_score
from .commission import calculate_commission_score
from .competition import calculate_competition_score
from .market_opportunity import calculate_market_opportunity_score
from .trend import calculate_trend_score
from .price import calculate_price_score
from .stock import calculate_stock_score


# ==========================================================
# MAIN
# ==========================================================

def calculate_opportunity(data):

    # ======================================================
    # CALCULATE EVERY SCORE
    # ======================================================

    scores = {

        "demand":
            calculate_demand_score(data),

        "conversion":
            calculate_conversion_score(data),

        "product_quality":
            calculate_product_quality_score(data),

        "trust":
            calculate_trust_score(data),

        "commission":
            calculate_commission_score(data),

        "competition":
            calculate_competition_score(data),

        "market":
            calculate_market_opportunity_score(data),

        "trend":
            calculate_trend_score(data),

        "price":
            calculate_price_score(data),

        "stock":
            calculate_stock_score(data),

    }

    # ======================================================
    # FINAL SCORE
    # ======================================================

    opportunity_score = 0

    for key, item in scores.items():

        opportunity_score += (

            item["score"]

            *

            WEIGHTS[key]

        )

    opportunity_score = round(
        opportunity_score,
        2
    )

    # ======================================================
    # FINAL RATING
    # ======================================================

    rating = get_rating(
        opportunity_score
    )

    # ======================================================
    # SUMMARY
    # ======================================================

    summary = generate_summary(
        scores
    )

    # ======================================================
    # RETURN
    # ======================================================

    return {

        "opportunity_score": opportunity_score,

        "rating": rating["rating"],

        "stars": rating["stars"],

        "status": rating["status"],

        "color": rating["color"],

        "summary": summary,

        "scores": scores

    }