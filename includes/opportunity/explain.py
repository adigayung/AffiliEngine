"""
Opportunity Engine V5

Explain Engine

Menghasilkan ringkasan analisis
berdasarkan seluruh score.
"""


def generate_summary(scores):

    summary = []

    for item in scores.values():

        if item.get("description"):

            summary.append(
                item["description"]
            )

    return summary