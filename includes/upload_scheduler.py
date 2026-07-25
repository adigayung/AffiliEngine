from collections import Counter
import random


MAX_CONSECUTIVE = 1


def generate_schedule(
    products: dict[str, int],
    max_consecutive: int = MAX_CONSECUTIVE,
    seed: int | None = None,
) -> list[str]:
    """
    Smart Smooth Weighted Round Robin

    Features:
    - Distribusi sesuai bobot
    - Tidak ada produk berturut-turut
    - Tie-break memakai produk yang paling lama tidak muncul
    - Jika masih seri diberi random kecil
    """

    rng = random.Random(seed)

    total_weight = sum(products.values())

    current = {name: 0 for name in products}
    remaining = products.copy()

    # terakhir muncul di index berapa
    last_seen = {name: -999999 for name in products}

    schedule = []

    while len(schedule) < total_weight:

        # Tambahkan score
        for name, weight in products.items():
            current[name] += weight

        candidates = []

        for name in products:

            if remaining[name] == 0:
                continue

            # Cek consecutive
            if len(schedule) >= max_consecutive:
                if all(x == name for x in schedule[-max_consecutive:]):

                    other_exist = any(
                        remaining[p] > 0 and p != name
                        for p in remaining
                    )

                    if other_exist:
                        continue

            candidates.append(name)

        # Hitung skor kandidat
        best_name = None
        best_score = None

        for name in candidates:

            score = (
                current[name],                      # prioritas utama
                len(schedule) - last_seen[name],    # paling lama tidak muncul
                rng.random(),                       # tie breaker terakhir
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

def create_upload_schedule(products, seed=None):
    return generate_schedule(products, seed=seed)

if __name__ == "__main__":

    products = {
        "Produk A": 10,
        "Produk B": 10,
        "Produk C": 10,
        "Produk D": 10,
    }

    # seed=None  -> hasil berbeda setiap generate
    # seed=12345 -> hasil selalu sama
    schedule = generate_schedule(products, seed=None)

    print("=== Jadwal ===")

    for i, product in enumerate(schedule, 1):
        print(f"{i:02d}. {product}")

    print("\n=== Total ===")

    counter = count_schedule(schedule)

    for product, total in counter.items():
        print(f"{product}: {total}")