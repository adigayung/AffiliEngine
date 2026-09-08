# File : includes/schedule/balanced.py
"""
Balanced Distribution

Metode penyebaran video alternatif untuk Generate Upload Schedule.

Tujuan
------
- Membuat penyebaran produk benar-benar merata sepanjang hari,
  bukan hanya merata pada satu sequence panjang.
- Setiap hari diusahakan sedekat mungkin dengan proporsi global
  (jumlah video produk / total video).
- Sisa pembagian (remainder / carry / error accumulation) dari satu
  hari dibawa ke hari berikutnya agar distribusi jangka panjang tetap
  seimbang.
- Jumlah upload per hari dipakai sebagai constraint melalui daftar
  kapasitas hari (day_capacities).
- Tidak ada pola yang di-hardcode; bekerja generik untuk berapa pun
  jumlah produk, jumlah video, jumlah upload per hari, dan jumlah hari.

Contoh
------
products  = {"A": 3, "B": 3, "C": 12}
day_cap   = [3, 3, 3, 3, 3, 3]   # 6 hari x 3 upload
hasil     = C A C | C B C | C A C | C B C | C A C | C B C
"""

from collections import Counter


def _arrange_day(counts: dict[str, int]) -> list[str]:
    """
    Mengurutkan isi satu hari agar produk yang sama tidak muncul
    berturut-turut selama masih memungkinkan.

    counts: {product: jumlah di hari tersebut}
    """
    remaining = dict(counts)
    order = []
    last = None

    while sum(remaining.values()) > 0:

        candidates = [
            name
            for name in remaining
            if remaining[name] > 0 and name != last
        ]

        # Jika tidak ada alternatif lain, terpaksa boleh sama dengan terakhir.
        if not candidates:
            candidates = [
                name
                for name in remaining
                if remaining[name] > 0
            ]

        candidates.sort(
            key=lambda name: (-remaining[name], name)
        )

        pick = candidates[0]

        order.append(pick)

        remaining[pick] -= 1

        last = pick

    return order


def _balanced_with_capacities(
    products: dict[str, int],
    day_capacities: list[int],
) -> list[str]:
    """
    Core Balanced Distribution.

    Mengisi slot per hari (day_capacities) sedekat mungkin dengan
    proporsi global, sambil membawa sisa (remainder) antar hari.

    Parameter
    ---------
    products        : {nama_produk: jumlah_video}
    day_capacities  : daftar jumlah upload untuk tiap hari.
                      Jumlah seluruh elemen harus == total video.

    Return
    ------
    list[str] : urutan produk (flat) hasil distribusi balanced.
                Setiap elemen = satu slot upload.
    """
    total = sum(products.values())

    if total <= 0:
        return []

    placed = {name: 0 for name in products}

    result = []

    slots_before = 0

    for cap in day_capacities:

        slots_after = slots_before + cap

        # Target kumulatif ideal produk tsb setelah hari ini selesai.
        frac = {
            name: products[name] * slots_after / total
            for name in products
        }

        # Kebutuhan integer minimum hari ini (selisih target kumulatif
        # dengan yang sudah ditempatkan), tidak melebihi sisa produk.
        need = {}

        for name in products:

            req = max(
                0,
                int(frac[name]) - placed[name]
            )

            req = min(
                req,
                products[name] - placed[name]
            )

            need[name] = req

        extra = cap - sum(need.values())

        # Slot sisa dibagikan ke produk dengan pecahan target terbesar
        # (largest remainder), selama masih punya stok.
        if extra > 0:

            order = sorted(
                products,
                key=lambda name: (frac[name] - int(frac[name]), name)
            )

            for name in reversed(order):

                if extra <= 0:
                    break

                if placed[name] + need[name] < products[name]:

                    need[name] += 1

                    extra -= 1

        # Pengaman: jika masih ada slot kosong, isi dari produk manapun
        # yang masih punya sisa.
        if extra > 0:

            for name in products:

                while (
                    extra > 0
                    and placed[name] + need[name] < products[name]
                ):

                    need[name] += 1

                    extra -= 1

        # Pengaman: jangan sampai kebutuhan melebihi kapasitas hari.
        over = sum(need.values()) - cap

        if over > 0:

            for name in products:

                while over > 0 and need[name] > 0:

                    need[name] -= 1

                    over -= 1

        # Susun urutan dalam hari (hindari produk sama berdekatan).
        result.extend(
            _arrange_day(
                {
                    name: need[name]
                    for name in products
                }
            )
        )

        for name in products:
            placed[name] += need[name]

        slots_before = slots_after

    # Jaminan akhir: setiap produk harus habis tepat.
    for name in products:
        if placed[name] != products[name]:
            raise ValueError(
                "Balanced Distribution gagal menjaga total "
                f"produk '{name}': {placed[name]} != {products[name]}"
            )

    if len(result) != total:
        raise ValueError(
            "Balanced Distribution menghasilkan jumlah slot "
            f"{len(result)} != total video {total}."
        )

    return result


def generate_balanced_schedule(
    products: dict[str, int],
    day_capacities: int | list[int],
) -> list[str]:
    """
    Membuat jadwal dengan Balanced Distribution.

    Parameter
    ---------
    products        : {nama_produk: jumlah_video}
    day_capacities  : int  = jumlah upload per hari (kapasitas sama tiap hari)
                      list = daftar kapasitas upload per hari,
                             (hari terakhir boleh lebih kecil).

    Return
    ------
    list[str] : urutan produk flat (satu elemen per slot upload).
    """
    total = sum(products.values())

    if total <= 0:
        return []

    if isinstance(day_capacities, int):

        daily = max(1, int(day_capacities))

        days = (total + daily - 1) // daily

        caps = [daily] * days

        remainder = total - (days - 1) * daily

        if remainder > 0:
            caps[-1] = remainder

    else:

        caps = [int(c) for c in day_capacities if int(c) > 0]

        if sum(caps) != total:
            raise ValueError(
                "Jumlah kapasitas hari tidak sama dengan total video: "
                f"{sum(caps)} != {total}"
            )

    return _balanced_with_capacities(
        products,
        caps,
    )
