# File : includes/verification_product.py

import re


def normalize_title(title: str) -> str:

    if not title:
        return ""

    title = title.lower().strip()

    # rapikan spasi
    title = re.sub(r"\s+", " ", title)

    return title


def compare_title(title_db: str, title_real: str) -> bool:

    db = normalize_title(title_db)
    real = normalize_title(title_real)

    # Android tidak boleh mengembalikan string kosong
    if not real:
        return False

    return db.startswith(real)