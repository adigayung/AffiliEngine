"""
Opportunity Engine V5

Rating akhir berdasarkan Opportunity Score.
"""


def get_rating(score):
    """
    Mengubah Opportunity Score menjadi rating.

    Return:
    {
        "rating": "A",
        "stars": 4,
        "status": "Strong",
        "color": "success"
    }
    """

    score = float(score)

    if score >= 95:
        return {
            "rating": "S",
            "stars": 5,
            "status": "Outstanding",
            "color": "lime",
        }

    if score >= 90:
        return {
            "rating": "A+",
            "stars": 5,
            "status": "Excellent",
            "color": "green",
        }

    if score >= 80:
        return {
            "rating": "A",
            "stars": 4,
            "status": "Strong",
            "color": "teal",
        }

    if score >= 70:
        return {
            "rating": "B+",
            "stars": 4,
            "status": "Good",
            "color": "cyan",
        }

    if score >= 60:
        return {
            "rating": "B",
            "stars": 3,
            "status": "Moderate",
            "color": "yellow",
        }

    if score >= 50:
        return {
            "rating": "C",
            "stars": 2,
            "status": "Weak",
            "color": "orange",
        }

    return {
        "rating": "D",
        "stars": 1,
        "status": "Poor",
        "color": "red",
    }