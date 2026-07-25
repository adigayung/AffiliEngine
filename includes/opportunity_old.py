import math


# ==========================================================
# HELPER
# ==========================================================

def normalize_log(value, max_value):
    value = max(float(value), 0)

    return min(
        (math.log10(value + 1) /
         math.log10(max_value + 1)) * 100,
        100
    )


def normalize_linear(value, max_value):
    value = max(float(value), 0)

    return min(
        (value / max_value) * 100,
        100
    )


# ==========================================================
# DEMAND
# ==========================================================

def calculate_demand_score(pesanan):
    return round(
        normalize_log(
            pesanan,
            1_000_000
        ),
        2
    )


# ==========================================================
# CTR
# ==========================================================

def calculate_conversion_score(ctr):
    return round(
        normalize_linear(
            ctr,
            20
        ),
        2
    )


# ==========================================================
# QUALITY
# ==========================================================

def calculate_quality_score(ulasan):
    return round(
        normalize_linear(
            ulasan,
            100
        ),
        2
    )


# ==========================================================
# COMMISSION
# ==========================================================

def calculate_commission_score(komisi):
    return round(
        normalize_linear(
            komisi,
            20
        ),
        2
    )


# ==========================================================
# MARKET OPPORTUNITY
# ==========================================================

def calculate_market_score(pesanan, kreator):
    """
    Mengukur peluang pasar.

    Rumus utama:

    Demand per Creator
    """

    kreator = max(float(kreator), 1)

    ratio = pesanan / kreator

    score = normalize_log(
        ratio,
        100
    )

    return round(score, 2), round(ratio, 2)


# ==========================================================
# RATING
# ==========================================================

def get_rating(score):

    if score >= 90:
        return "A+", 5, "Excellent"

    elif score >= 80:
        return "A", 4, "Strong"

    elif score >= 70:
        return "B+", 3, "Good"

    elif score >= 60:
        return "B", 2, "Moderate"

    else:
        return "C", 1, "Weak"


# ==========================================================
# MAIN
# ==========================================================

def calculate_opportunity(data):

    pesanan = float(data.get("pesanan", 0))
    ctr = float(data.get("ctr", 0))
    ulasan = float(data.get("ulasan_positif", 0))
    komisi = float(data.get("komisi", 0))
    kreator = float(data.get("jumlah_kreator", 1))

    demand_score = calculate_demand_score(
        pesanan
    )

    conversion_score = calculate_conversion_score(
        ctr
    )

    quality_score = calculate_quality_score(
        ulasan
    )

    commission_score = calculate_commission_score(
        komisi
    )

    market_score, ratio = calculate_market_score(
        pesanan,
        kreator
    )

    opportunity_score = round(

        demand_score * 0.28 +

        conversion_score * 0.22 +

        quality_score * 0.20 +

        commission_score * 0.15 +

        market_score * 0.15,

        2
    )

    rating, stars, status = get_rating(
        opportunity_score
    )

    return {

        "opportunity_score": opportunity_score,

        "rating": rating,

        "stars": stars,

        "status": status,

        "demand_per_creator": ratio,

        "demand_score": demand_score,

        "conversion_score": conversion_score,

        "quality_score": quality_score,

        "commission_score": commission_score,

        "market_score": market_score
    }