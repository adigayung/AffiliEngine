"""
scraper.py - Ambil metadata Shopee Product.

Menggunakan existing Chromium driver dari
`includes/tiktok_scrape_videos/driver.py` dengan `profile_path="./chromium"`
(JANGAN membuat browser automation baru).

Alur:
    1. Buka affiliate URL (https://s.shopee.co.id/<code>)
    2. Ikuti redirect ke halaman produk Shopee
    3. Ambil metadata dari sumber data asli halaman (bertingkat):

       a. PDP API `/api/v4/pdp/get_pc` (ditangkap dari fetch di browser,
          session profile persistent ikut terpakai) — sumber terbaik:
          item_id, shop_id, title, price, rating, review_count, sold
       b. URL hasil redirect   -> product_id, shop_id
       c. SSR HTML / title tag -> title, product_id, shop_id, description
       d. Rendered DOM innerText -> price, sold, rating, review_count

    Semua nilai diambil dari halaman; field yang tidak ditemukan -> None.

PENTING:
    - Affiliate URL asli TIDAK pernah diubah / disimpan di sini.
      Service yang bertanggung jawab menyimpan `url_link` = affiliate URL.
    - URL hasil redirect hanya digunakan sementara untuk mengambil metadata.
"""

import re
import time
import json
import logging

from includes.tiktok_scrape_videos.driver import create_driver

logger = logging.getLogger(__name__)

# Profile Chromium existing (sama dengan video_performance/scanner.py)
PROFILE_PATH = "./chromium"

# Timeout tunggu redirect keluar dari s.shopee.co.id
REDIRECT_TIMEOUT = 60

# Timeout tunggu data produk muncul
DATA_TIMEOUT = 40

# Jeda singkat agar SPA selesai render/hydrate
SETTLE_TIME = 4

# ----------------------------------------------------------------------
# Capture respons PDP API via monkey-patch fetch.
# Script ini di-inject via CDP SEBELUM navigasi sehingga berlaku untuk
# semua dokumen; hasilnya hanya disimpan di memori browser.
# ----------------------------------------------------------------------
CAPTURE_JS = """
window.__xhr_captured = [];
(function() {
  var origFetch = window.fetch;
  if (origFetch) {
    window.fetch = function() {
      var url = (typeof arguments[0] === 'string') ? arguments[0] : (arguments[0] && arguments[0].url);
      return origFetch.apply(this, arguments).then(function(resp) {
        try {
          if (url && url.indexOf('/api/v4/pdp/get_pc') >= 0) {
            resp.clone().text().then(function(t) {
              window.__xhr_captured.push({url: url, body: t.slice(0, 3000000)});
            });
          }
        } catch(e) {}
        return resp;
      });
    };
  }
})();
"""


def _get_captured_pdp(driver):
    """Ambil respons PDP API dari memori browser (atau None)."""
    try:
        captured = driver.execute_script("return window.__xhr_captured || [];")
    except Exception:
        return None
    for entry in captured:
        if "/api/v4/pdp/get_pc" in (entry.get("url") or ""):
            try:
                return json.loads(entry.get("body") or "{}")
            except Exception:
                return None
    return None


# ----------------------------------------------------------------------
# Parser angka (format Indonesia: RB=ribu, JT=juta)
# ----------------------------------------------------------------------
def _parse_count_text(text):
    """
    "10RB+"  -> 10000
    "1,5RB"  -> 1500
    "2JT"    -> 2000000
    "1,2JT"  -> 1200000
    "500"    -> 500
    """
    if not text:
        return None
    text = str(text).strip().replace(" ", "").upper().rstrip("+")
    mult = 1
    if text.endswith("JT"):
        mult = 1000000
        text = text[:-2]
    elif text.endswith("RB"):
        mult = 1000
        text = text[:-2]
    elif text.endswith("K"):
        mult = 1000
        text = text[:-1]
    text = text.replace(".", "").replace(",", ".")
    try:
        return int(float(text) * mult)
    except ValueError:
        return None


def _parse_idr_text(text):
    """'25.000' -> 25000 ; 'Rp25.000' -> 25000"""
    if not text:
        return None
    text = str(text).replace("Rp", "").replace(" ", "")
    text = text.replace(".", "").replace(",", "")
    try:
        return int(text)
    except ValueError:
        return None


# ----------------------------------------------------------------------
# Sumber 1: PDP API
# ----------------------------------------------------------------------
def _extract_from_pdp(pdp):
    """Metadata dari respons API /api/v4/pdp/get_pc."""
    d = pdp.get("data") or {}
    item = d.get("item") or {}
    review = d.get("product_review") or {}
    price_blk = d.get("product_price") or {}
    shop = d.get("shop_detailed") or {}

    meta = {
        "product_id": item.get("item_id"),
        "shop_id": item.get("shop_id"),
        "title": item.get("title"),
        "description": item.get("description"),
        "price": None,
        "sold_count": None,
        "rating": None,
        "review_count": None,
    }

    # --- PRICE: satuan API = IDR x 100000 ---
    raw = None
    p = price_blk.get("price") or {}
    if p.get("single_value") and int(p["single_value"]) > 0:
        raw = int(p["single_value"])
    elif p.get("range_min") and int(p["range_min"]) > 0:
        raw = int(p["range_min"])
    if not raw:
        raw = item.get("price_min") or item.get("price")
    if raw:
        meta["price"] = int(raw) // 100000

    # --- RATING (bulatkan ke 2 desimal, konsisten dgn DECIMAL(3,2)) ---
    rating = review.get("rating_star") or (item.get("item_rating") or {}).get("rating_star")
    if rating is not None:
        try:
            meta["rating"] = round(float(rating), 2)
        except (TypeError, ValueError):
            meta["rating"] = None

    # --- REVIEW COUNT ---
    meta["review_count"] = review.get("total_rating_count") or review.get("cmt_count")

    # --- SOLD ---
    sold = _parse_count_text(
        review.get("sold_count_display")
        or review.get("historical_sold_display")
        or review.get("global_sold_display")
    )
    if not sold:
        sold = review.get("historical_sold") or review.get("global_sold")
    meta["sold_count"] = sold

    return meta


# ----------------------------------------------------------------------
# Sumber 2: URL hasil redirect
# ----------------------------------------------------------------------
def _extract_from_url(final_url, meta):
    m = re.search(r"/product/(\d+)/(\d+)", final_url or "")
    if m:
        meta.setdefault("shop_id", m.group(1))
        meta.setdefault("product_id", m.group(2))
    if not meta.get("product_id"):
        m = re.search(r"-i\.(\d+)\.(\d+)", final_url or "")
        if m:
            meta.setdefault("shop_id", m.group(1))
            meta.setdefault("product_id", m.group(2))
    return meta


# ----------------------------------------------------------------------
# Sumber 3: SSR HTML / title tag
# ----------------------------------------------------------------------
def _extract_from_html(html, meta):
    m = re.search(r"<title>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    if m and not meta.get("title"):
        title = re.sub(
            r"\s*[-–—|]\s*Shopee\s+Indonesia\s*$",
            "",
            m.group(1).strip(),
        )
        if title:
            meta["title"] = title

    if not meta.get("title"):
        m = re.search(r'property="og:title"\s+content="([^"]*)"', html, re.IGNORECASE)
        if m:
            meta["title"] = m.group(1).strip()

    m = re.search(r'"item_id"\s*:\s*"?(\d+)"?', html)
    if m and not meta.get("product_id"):
        meta["product_id"] = m.group(1)
    m = re.search(r'"shop_id"\s*:\s*"?(\d+)"?', html)
    if m and not meta.get("shop_id"):
        meta["shop_id"] = m.group(1)

    if not meta.get("description"):
        m = re.search(r'name="description"\s+content="([^"]*)"', html, re.IGNORECASE)
        if m:
            meta["description"] = m.group(1).strip()

    return meta


# ----------------------------------------------------------------------
# Sumber 4: rendered DOM innerText
# ----------------------------------------------------------------------
def _extract_from_dom(inner_text, meta):
    if not inner_text:
        return meta

    if not meta.get("price"):
        m = re.search(r"Rp\s*([\d.,]+)", inner_text)
        if m:
            meta["price"] = _parse_idr_text(m.group(1))

    if not meta.get("sold_count"):
        m = re.search(r"([\d.,]+\s?(?:RB|JT|K)?\+?)\s*Terjual", inner_text)
        if m:
            meta["sold_count"] = _parse_count_text(m.group(1))

    if not meta.get("rating"):
        m = re.search(r"(\d[.,]\d)\s*[\d.,]+\s*(?:RB|JT|K)?\+?\s*Penilaian", inner_text)
        if m:
            try:
                meta["rating"] = round(float(m.group(1).replace(",", ".")), 2)
            except ValueError:
                pass

    if not meta.get("review_count"):
        m = re.search(r"([\d.,]+\s?(?:RB|JT|K)?)\s*Penilaian", inner_text)
        if m:
            meta["review_count"] = _parse_count_text(m.group(1))

    return meta


def _build_metadata(driver, final_url, html):
    """Gabungkan metadata dari semua sumber (PDP API -> URL -> HTML -> DOM)."""
    meta = {}

    pdp = _get_captured_pdp(driver)
    if pdp:
        meta = _extract_from_pdp(pdp)
        logger.info("Sumber metadata: PDP API (/api/v4/pdp/get_pc)")
    else:
        logger.info("Sumber metadata: URL + SSR HTML + DOM (PDP API tidak tertangkap)")

    meta = _extract_from_url(final_url, meta)
    meta = _extract_from_html(html, meta)

    try:
        inner_text = driver.execute_script("return document.body.innerText;") or ""
    except Exception:
        inner_text = ""
    meta = _extract_from_dom(inner_text, meta)

    return meta


def fetch_shopee_metadata(affiliate_url):
    """
    Buka affiliate URL dengan existing driver, ikuti redirect,
    lalu ambil metadata produk Shopee.

    Args:
        affiliate_url: Affiliate URL asli (https://s.shopee.co.id/<code>)

    Returns:
        dict: Metadata produk dengan keys:
            product_id, shop_id, title, description, price,
            commission_rate, sold_count, rating, review_count

        product_id bisa None jika halaman bukan halaman produk.

    Raises:
        TimeoutException: jika redirect / data tidak muncul dalam batas waktu
        Exception: error browser lain
    """
    driver = None

    try:
        driver = create_driver(profile_path=PROFILE_PATH)

        # Inject capture PDP API sebelum navigasi (opsional, tidak fatal)
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": CAPTURE_JS},
            )
        except Exception:
            logger.warning("CDP injection gagal; akan fallback ke DOM/SSR")

        logger.info("Buka affiliate URL: %s", affiliate_url)
        driver.get(affiliate_url)

        # ----------------------------------------------------------
        # Tunggu redirect keluar dari s.shopee.co.id
        # ----------------------------------------------------------
        final_url = driver.current_url or ""
        start = time.time()
        while "s.shopee.co.id" in final_url and (time.time() - start) < REDIRECT_TIMEOUT:
            time.sleep(1)
            try:
                final_url = driver.current_url or ""
            except Exception:
                break

        logger.info("Redirect ke: %s", final_url)

        # ----------------------------------------------------------
        # Tunggu data produk muncul (SSR JSON / PDP API)
        # ----------------------------------------------------------
        html = driver.page_source or ""
        start = time.time()
        while (
            "itemid" not in html
            and "item_id" not in html
            and not _get_captured_pdp(driver)
            and (time.time() - start) < DATA_TIMEOUT
        ):
            time.sleep(1)
            try:
                html = driver.page_source or ""
            except Exception:
                break

        time.sleep(SETTLE_TIME)
        html = driver.page_source or ""

        metadata = _build_metadata(driver, final_url, html)

        # Pastikan selalu ada key yang diharapkan service
        metadata.setdefault("product_id", None)
        metadata.setdefault("shop_id", None)
        metadata.setdefault("title", None)
        metadata.setdefault("description", None)
        metadata.setdefault("price", None)
        metadata.setdefault("commission_rate", None)
        metadata.setdefault("sold_count", None)
        metadata.setdefault("rating", None)
        metadata.setdefault("review_count", None)

        return metadata

    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
