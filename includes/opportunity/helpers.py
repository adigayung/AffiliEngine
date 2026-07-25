# FILE : includes\opportunity\helpers.py
import math

# ==========================================================
# BASIC
# ==========================================================

def clamp(value, minimum=0, maximum=100):
    """
    Membatasi nilai agar berada di antara minimum dan maximum.
    """
    return max(minimum, min(float(value), maximum))


# ==========================================================
# NORMALIZE
# ==========================================================

def normalize_linear(value, max_value):
    """
    Normalisasi linear menjadi 0-100
    """

    value = max(float(value), 0)

    if max_value <= 0:
        return 0

    return clamp(
        (value / max_value) * 100
    )


def normalize_log(value, max_value):
    """
    Normalisasi logaritmik.
    Cocok untuk:
    - Pesanan
    - Vote
    - Sold
    - Keranjang
    - Creator
    """

    value = max(float(value), 0)

    if max_value <= 0:
        return 0

    score = (
        math.log10(value + 1)
        /
        math.log10(max_value + 1)
    ) * 100

    return clamp(score)


def normalize_inverse(value, max_value):
    """
    Semakin kecil semakin bagus.

    Contoh:
    Jumlah kreator.
    """

    value = max(float(value), 0)

    if max_value <= 0:
        return 100

    score = 100 - (
        (value / max_value) * 100
    )

    return clamp(score)

def normalize_inverse_log(value, max_value):

    value = max(float(value), 0)

    if max_value <= 0:
        return 100

    score = (
        1 -
        math.log10(value + 1) /
        math.log10(max_value + 1)
    ) * 100

    return clamp(score)

# ==========================================================
# CURVE
# ==========================================================

def sigmoid(
    value,
    midpoint,
    steepness=1
):
    """
    Kurva sigmoid.

    Berguna untuk:
    - Commission
    - Price
    - Trend
    """

    x = float(value)

    score = (
        1 /
        (
            1 +
            math.exp(
                -steepness * (x - midpoint)
            )
        )
    ) * 100

    return clamp(score)


# ==========================================================
# STATUS
# ==========================================================

def get_status(score):

    score = clamp(score)

    if score >= 90:
        return "Excellent"

    if score >= 80:
        return "Strong"

    if score >= 70:
        return "Good"

    if score >= 60:
        return "Moderate"

    return "Weak"


# ==========================================================
# SCORE OBJECT
# ==========================================================

def make_score(
    name,
    score,
    value=None,
    description=""
):
    """
    Format standar semua module.
    """

    score = round(
        clamp(score),
        2
    )

    return {
        "name": name,
        "score": score,
        "status": get_status(score),
        "value": value,
        "description": description,
    }