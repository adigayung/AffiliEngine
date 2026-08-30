import re

def str_k_to_int(text):
    """
    Convert:
    2K      -> 2000
    2.0K    -> 2000
    8.1K    -> 8100
    15.8K   -> 15800
    1M      -> 1000000
    1.5M    -> 1500000
    999     -> 999
    """

    if text is None:
        return 0

    text = str(text).strip().upper().replace(" ", "")

    if text == "":
        return 0

    try:

        if text.endswith("K"):
            return int(float(text[:-1]) * 1000)

        if text.endswith("M"):
            return int(float(text[:-1]) * 1000000)

        return int(float(text.replace(",", "")))

    except:
        return 0

def convert_number(text):
    if text is None:
        return None

    txt = str(text).upper().strip()

    # Perbaikan OCR
    txt = txt.replace("I", "1")
    txt = txt.replace("L", "1")
    txt = txt.replace("O", "0")

    # Hapus prefix
    txt = txt.replace("RP", "").strip()

    # ------------------------
    # Persen
    # Contoh: 6,29%
    # ------------------------
    if "%" in txt:
        txt = txt.replace("%", "").replace(",", ".")
        try:
            return int(float(txt) * 10) / 10
        except:
            return None

    # ------------------------
    # Ribuan
    # Contoh: 1,3K -> 1300
    # ------------------------
    if txt.endswith("K"):
        txt = txt[:-1].replace(",", ".")
        try:
            return int(float(txt) * 1000)
        except:
            return None

    # ------------------------
    # Desimal
    # Contoh: 6,29 -> 6.29
    # ------------------------
    if "," in txt:
        txt = txt.replace(",", ".")
        try:
            return float(txt)
        except:
            return None

    # ------------------------
    # Angka biasa / Rupiah
    # Contoh: 2.392 -> 2392
    # ------------------------
    txt = txt.replace(".", "")

    if txt.isdigit():
        return int(txt)

    return None


def split_per(text):

    idx = text.lower().find("per")

    if idx == -1:
        return text, ""

    kiri = text[:idx].strip()
    kanan = text[idx:].strip()

    return kiri, kanan


def parse_ocr(data):

    hasil = {
        "komisi": None,
        "persentase_komisi": None,
        "stok": None,
        "ulasan": None,
        "pesanan": None,
        "ctr": None,
        "kreator": None,
        "keranjang": None
    }

    # True bila ulasan sudah terisi dari rating "Skor produk" X/5.0
    # (PRIORITAS 1) -> hitungan ulasan UI lama tidak boleh menimpanya.
    ulasan_dari_rating = False

    for item in data:

        low = item.lower()

        # ====================================================
        # Komisi
        # ====================================================
        if "dapatkan" in low:

            m = re.search(
                r'rp\s*([0-9.,klioam]+)',
                low,
                re.IGNORECASE
            )
            if m:
                hasil["komisi"] = convert_number(
                    m.group(1)
                )

        # ====================================================
        # Perse mendapatkan stok barang
        # ====================================================
        elif "stok" in low:

            m = re.match(
                r'\s*([\d.,]+(?:\.?[klioam]{1,2})?)\s+stok\s+tersedia',
                low,
                re.IGNORECASE
            )

            if m:
                hasil["stok"] = convert_number(
                    m.group(1)
                )

        # ====================================================
        # Persentase Komisi
        # ====================================================
        if "persentase" in low or "komisi" in low:
                    m = re.search(
                        r'(?:persentase\s+)?komisi\s*(\d+(?:[.,]\d+)?)\s*%',
                        low,
                        re.IGNORECASE
                    )
                    if m:
                        hasil["persentase_komisi"] = float(
                            m.group(1).replace(",", ".")
                        )
        # ====================================================
        # Ulasan
        # ====================================================

        elif "ulasan" in low:

            # PRIORITAS 1 — UI baru: rating "Skor produk" X/5.0
            # contoh crop: "ulasan 4.0/5.0" -> ulasan = 4.0
            m_rating = re.search(
                r'([\d.,Oo]+)\s*/\s*5(?:[.Oo]0)?',
                low
            )

            if m_rating:

                try:

                    hasil["ulasan"] = float(
                        m_rating.group(1)
                        .replace("O", "0")
                        .replace("o", "0")
                        .replace(",", ".")
                    )

                    ulasan_dari_rating = True

                except:

                    hasil["ulasan"] = None

            # PRIORITAS 2/3 — UI lama / fallback: hitungan ulasan
            elif not ulasan_dari_rating:

                value = (
                    low
                    .replace("ulasan positif", "")
                    .replace("ulasan", "")
                    .replace("positif", "")
                    .strip()
                )

                hasil["ulasan"] = convert_number(value)

        # ====================================================
        # Pesanan
        # ====================================================

        elif "pesanan" in low:

            value = low.replace(
                "pesanan",
                ""
            ).strip()

            hasil["pesanan"] = convert_number(value)

        # ====================================================
        # CTR
        # ====================================================

        elif "ctr" in low:

            value = low.replace(
                "ctr",
                ""
            ).strip()

            hasil["ctr"] = convert_number(value)

        # ====================================================
        # Kreator
        # ====================================================

        elif "jumlah kreator" in low:

            value = low.replace(
                "jumlah kreator",
                ""
            ).strip()

            hasil["kreator"] = convert_number(value)

        # ====================================================
        # Keranjang
        # ====================================================

        elif "keranjang" in low:

            value = (
                low.replace(
                    "pembeli yang menambahkan ke keranjang",
                    ""
                ).strip()
            )

            hasil["keranjang"] = convert_number(value)
    print("=" * 80)
    print(" data Di terima : ")
    print(data)

    print(" Hasilnya : ")
    print(hasil)
    print("=" * 80)
    return hasil
