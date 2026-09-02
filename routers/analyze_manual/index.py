# routers/analyze_manual/index.py
"""
Manual TikTok Metrics Analysis

Jalur analisis baru: user mengetik metrik TikTok secara manual,
sementara data produk tetap di-scrape dari URL via get_info_tt_from_url()
(termasuk di dalam analyze_product).

Alur:
    manual metrics + product URL
        -> validate input manual
        -> analyze_product(image=None, raw_data=manual_data)
        -> get_info_tt_from_url()  (data produk)
        -> extracted_data
        -> calculate_opportunity()
        -> LLM (enable_llm=True)
        -> save_product / save_product_analysis / save_llm_analysis

Pipeline OCR existing (analyze_by_phone) TIDAK disentuh.
"""

import re
from urllib.parse import urlparse

from flask import Blueprint, render_template, request

from includes.product_analyzer import analyze_product
from includes.logFX import logger

analyze_manual_bp = Blueprint(
    "analyze_manual",
    __name__,
    url_prefix="/analyze-manual"
)

# Regex ketat: hanya angka (tanpa Rp, %, k, K, koma, minus).
_INT_RE = re.compile(r"^\d+$")
_DEC_RE = re.compile(r"^\d+(\.\d+)?$")


def _validate_int(value, label, min_value=0):
    """Bilangan bulat >= min_value. Return (parsed, error)."""
    value = (value or "").strip()
    if not value:
        return None, f"{label} wajib diisi."
    if not _INT_RE.match(value):
        return None, (
            f"{label} harus berupa bilangan bulat "
            f"(tanpa Rp, %, titik, atau koma)."
        )
    parsed = int(value)
    if parsed < min_value:
        return None, f"{label} minimal {min_value}."
    return parsed, None


def _validate_decimal(value, label, min_value=None, max_value=None):
    """Angka desimal dalam rentang. Return (parsed, error)."""
    value = (value or "").strip()
    if not value:
        return None, f"{label} wajib diisi."
    if not _DEC_RE.match(value):
        return None, (
            f"{label} harus berupa angka desimal valid "
            f"(contoh: 10 atau 6.7, tanpa simbol)."
        )
    parsed = float(value)
    if min_value is not None and parsed < min_value:
        return None, f"{label} minimal {min_value}."
    if max_value is not None and parsed > max_value:
        return None, f"{label} maksimal {max_value}."
    return parsed, None


def _validate_url(value):
    """URL http/https wajib dan valid. Return (parsed, error)."""
    value = (value or "").strip()
    if not value:
        return None, "URL Product wajib diisi."
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None, (
            "URL Product tidak valid. "
            "Gunakan format https://vt.tokopedia.com/t/..."
        )
    return value, None


@analyze_manual_bp.route("/")
def index():
    return render_template(
        "analyze_manual/index.html",
        page_title="Manual Analysis",
        errors={},
        form=None
    )


@analyze_manual_bp.route("/analyze", methods=["POST"])
def analyze():
    form = request.form
    errors = {}

    # ==================================================
    # Validasi semua input manual (jangan submit bila invalid)
    # ==================================================

    komisi, err = _validate_int(
        form.get("komisi"), "Nominal Komisi", min_value=0
    )
    if err:
        errors["komisi"] = err

    persentase_komisi, err = _validate_decimal(
        form.get("persentase_komisi"),
        "Persentase Komisi",
        min_value=0,
        max_value=100
    )
    if err:
        errors["persentase_komisi"] = err

    rating, err = _validate_decimal(
        form.get("rating"),
        "Produk Rating",
        min_value=1.0,
        max_value=5.0
    )
    if err:
        errors["rating"] = err

    pesanan, err = _validate_int(
        form.get("pesanan"), "Pesanan", min_value=0
    )
    if err:
        errors["pesanan"] = err

    ctr, err = _validate_decimal(
        form.get("ctr"),
        "CTR",
        min_value=0,
        max_value=100
    )
    if err:
        errors["ctr"] = err

    jumlah_kreator, err = _validate_int(
        form.get("jumlah_kreator"), "Jumlah Creator", min_value=0
    )
    if err:
        errors["jumlah_kreator"] = err

    pembeli_keranjang, err = _validate_int(
        form.get("pembeli_keranjang"),
        "Pembeli yang Menambahkan ke Keranjang",
        min_value=0
    )
    if err:
        errors["pembeli_keranjang"] = err

    url, err = _validate_url(form.get("product_link"))
    if err:
        errors["product_link"] = err

    if errors:
        return render_template(
            "analyze_manual/index.html",
            page_title="Manual Analysis",
            errors=errors,
            form=form
        )

    # ==================================================
    # Struktur data manual -> sama persis dengan raw OCR
    # yang dikonsumsi analyze_product() / opportunity engine:
    #   "kreator"   -> extracted_data["jumlah_kreator"]
    #   "keranjang" -> extracted_data["pembeli_keranjang"]
    # ==================================================

    manual_data = {
        "komisi": komisi,
        "persentase_komisi": persentase_komisi,
        "rating": rating,
        "pesanan": pesanan,
        "ctr": ctr,
        "kreator": jumlah_kreator,
        "keranjang": pembeli_keranjang,
    }

    # ==================================================
    # Jalankan pipeline existing (tanpa OCR, tanpa image)
    # ==================================================

    try:
        result = analyze_product(
            image=None,
            product_link=url,
            enable_llm=True,
            raw_data=manual_data
        )
    except Exception as e:
        logger("error", f"Manual analysis gagal: {e}")
        errors["global"] = f"Analisis gagal: {e}"
        return render_template(
            "analyze_manual/index.html",
            page_title="Manual Analysis",
            errors=errors,
            form=form
        )

    return render_template(
        "analyze_manual/index.html",
        page_title="Manual Analysis",
        text=result["product"],
        analysis=result["analysis"],
        hasil_llm=result["hasil_llm"],
        errors={},
        form=None
    )
