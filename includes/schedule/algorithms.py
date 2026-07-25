# File : includes/schedule/algorithms.py

from collections import Counter
import random

MAX_CONSECUTIVE = 1

def create_upload_schedule(
    products: dict[str, int],
    max_consecutive: int = MAX_CONSECUTIVE,
    seed: int | None = None,
) -> list[str]:
    """
    Smart Smooth Weighted Round Robin

    Features
    --------
    - Distribusi sesuai bobot.
    - Menghindari produk berturut-turut.
    - Tie-break berdasarkan produk yang paling lama tidak muncul.
    - Random kecil sebagai tie-break terakhir.
    """

    rng = random.Random(seed)

    total_weight = sum(products.values())

    current = {
        name: 0
        for name in products
    }

    remaining = products.copy()

    last_seen = {
        name: -999999
        for name in products
    }

    schedule = []

    while len(schedule) < total_weight:

        for name, weight in products.items():

            current[name] += weight

        candidates = []

        for name in products:

            if remaining[name] == 0:

                continue

            if len(schedule) >= max_consecutive:

                if all(
                    x == name
                    for x in schedule[-max_consecutive:]
                ):

                    other_exist = any(
                        remaining[p] > 0 and p != name
                        for p in remaining
                    )

                    if other_exist:

                        continue

            candidates.append(name)

        best_name = None

        best_score = None

        for name in candidates:

            score = (

                current[name],

                len(schedule) - last_seen[name],

                rng.random()

            )

            if best_score is None or score > best_score:

                best_score = score

                best_name = name

        selected = best_name

        schedule.append(selected)

        remaining[selected] -= 1

        current[selected] -= total_weight

        last_seen[selected] = len(schedule)

    return schedule


def count_schedule(schedule):

    return Counter(schedule)


