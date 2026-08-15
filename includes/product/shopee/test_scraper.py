"""
test_scraper.py - TESTER TERPISAH untuk scraper Shopee.

Tester ini MEMBUKA browser nyata dengan profile persistent yang sudah
login ke Shopee, membuka affiliate URL, mengikuti redirect, lalu
mengambil metadata produk. HASIL HANYA DITAMPILKAN DI TERMINAL —
TIDAK ADA SATU PUN DATA YANG DITULIS KE DATABASE.

Driver:
    includes/tiktok_scrape_videos/driver.py -> create_driver(profile_path="./chromium")

Strategi ambil metadata (bertingkat, sumber asli dari halaman — tidak mengarang):
    1. URL hasil redirect        -> product_id, shop_id
    2. PDP API (XHR/fetch)       -> item_id, shop_id, title, price, rating,
                                    review_count, sold (sumber terbaik)
    3. SSR JSON (PDP_BFF_DATA)   -> title, product_id, shop_id (fallback)
    4. Rendered DOM (innerText)  -> price, sold, rating, review_count (fallback)

Cara menjalankan:
    python includes/product/shopee/test_scraper.py

Status yang dideteksi:
    A. Produk berhasil dibuka
    B. SHOPEE LOGIN REQUIRED
    C. Redirect gagal
    D. Halaman tidak ditemukan
    E. Timeout
"""

import os
import re
import sys
import time
import json
import logging

# Pastikan root project ada di sys.path agar import "includes.*" berhasil
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from includes.tiktok_scrape_videos.driver import create_driver

logging.basicConfig(level=logging.WARNING)

# ============================================================
# KONFIGURASI TEST
# ============================================================
PROFILE_PATH = "./chromium"
AFFILIATE_URL = "https://s.shopee.co.id/5VUY8pxMv5"

REDIRECT_TIMEOUT = 60      # detik menunggu redirect keluar dari s.shopee.co.id
DATA_TIMEOUT = 40          # detik menunggu data produk muncul
SETTLE_TIME = 4            # jeda agar SPA selesai render/hydrate

DEBUG_HTML_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "_tmp_shopee_page.html",
)

# ============================================================
# CAPTURE PDP API (fetch monkey-patch via CDP, jalan sebelum
# semua script halaman; hanya menyimpan di memori browser,
# TIDAK menulis ke database)
# ============================================================
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


def inject_pdp_capture(driver):
    """Inject capture script agar berlaku untuk dokumen apa pun."""
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": CAPTURE_JS},
        )
        return True
    except Exception as e:
        print("    [CDP injection error]", e)
        return False


def get_captured_pdp(driver):
    """Ambil respons PDP API dari memori browser."""
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


# ============================================================
# PARSER ANGKA (format Indonesia)
# ============================================================
def parse_count_text(text):
    """
    "10RB+"  -> 10000
    "1,5RB"  -> 1500
    "2JT"    -> 2000000
    "1,2JT"  -> 1200000
    "500"    -> 500
    """
    if not text:
        return None
    text = text.strip().replace(" ", "").upper().rstrip("+")
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


def parse_idr_text(text):
    """'25.000' -> 25000 ; 'Rp25.000' -> 25000"""
    if not text:
        return None
    text = text.replace("Rp", "").replace(" ", "")
    text = text.replace(".", "").replace(",", "")
    try:
        return int(text)
    except ValueError:
        return None


# ============================================================
# EKSTRAKSI METADATA (sumber 1: PDP API)
# ============================================================
def extract_from_pdp(pdp):
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
        "shop_name": shop.get("name"),
        "shop_location": item.get("shop_location"),
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

    # --- RATING (bulatkan ke 2 desimal agar konsisten dgn DECIMAL(3,2)) ---
    rating = review.get("rating_star") or (item.get("item_rating") or {}).get("rating_star")
    if rating is not None:
        try:
            meta["rating"] = round(float(rating), 2)
        except (TypeError, ValueError):
            meta["rating"] = None

    # --- REVIEW COUNT ---
    meta["review_count"] = review.get("total_rating_count") or review.get("cmt_count")

    # --- SOLD ---
    sold = parse_count_text(
        review.get("sold_count_display")
        or review.get("historical_sold_display")
        or review.get("global_sold_display")
    )
    if not sold:
        sold = review.get("historical_sold") or review.get("global_sold")
    meta["sold_count"] = sold

    return meta


# ============================================================
# EKSTRAKSI METADATA (sumber 2: URL hasil redirect)
# ============================================================
def extract_from_url(final_url, meta):
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


# ============================================================
# EKSTRAKSI METADATA (sumber 3: SSR JSON + title tag)
# ============================================================
def extract_from_html(html, meta):
    # Title dari <title> tag
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

    # product_id / shop_id dari SSR JSON (PDP_BFF_DATA)
    m = re.search(r'"item_id"\s*:\s*"?(\d+)"?', html)
    if m and not meta.get("product_id"):
        meta["product_id"] = m.group(1)
    m = re.search(r'"shop_id"\s*:\s*"?(\d+)"?', html)
    if m and not meta.get("shop_id"):
        meta["shop_id"] = m.group(1)

    # description meta
    if not meta.get("description"):
        m = re.search(r'name="description"\s+content="([^"]*)"', html, re.IGNORECASE)
        if m:
            meta["description"] = m.group(1).strip()

    return meta


# ============================================================
# EKSTRAKSI METADATA (sumber 4: rendered DOM innerText)
# ============================================================
def extract_from_dom(inner_text, meta):
    if not inner_text:
        return meta

    # PRICE: "Rp25.000 - Rp32.000" / "Rp25.000"
    if not meta.get("price"):
        m = re.search(r"Rp\s*([\d.,]+)", inner_text)
        if m:
            meta["price"] = parse_idr_text(m.group(1))

    # SOLD: "10RB+ Terjual"
    if not meta.get("sold_count"):
        m = re.search(r"([\d.,]+\s?(?:RB|JT|K)?\+?)\s*Terjual", inner_text)
        if m:
            meta["sold_count"] = parse_count_text(m.group(1))

    # RATING: "4.5" sebelum "9,6RB Penilaian"
    if not meta.get("rating"):
        m = re.search(r"(\d[.,]\d)\s*[\d.,]+\s*(?:RB|JT|K)?\+?\s*Penilaian", inner_text)
        if m:
            try:
                meta["rating"] = float(m.group(1).replace(",", "."))
            except ValueError:
                pass

    # REVIEW COUNT: "9,6RB Penilaian"
    if not meta.get("review_count"):
        m = re.search(r"([\d.,]+\s?(?:RB|JT|K)?)\s*Penilaian", inner_text)
        if m:
            meta["review_count"] = parse_count_text(m.group(1))

    return meta


# ============================================================
# DETEKSI STATUS HALAMAN
# ============================================================
def is_product_page(driver):
    url = driver.current_url or ""
    if re.search(r"/product/\d+/\d+", url):
        return True
    if re.search(r"-i\.\d+\.\d+", url):
        return True
    try:
        html = driver.page_source or ""
        if "route_product_id" in html or '"itemid"' in html:
            return True
    except Exception:
        pass
    return False


def is_shopee_login_required(driver):
    if is_product_page(driver):
        return False
    url = ""
    try:
        url = (driver.current_url or "").lower()
    except Exception:
        pass
    strong_url = [
        "account.shopee", "/buyer/login", "/login", "passkey",
        "kms-auth", "authorize",
    ]
    if any(ind in url for ind in strong_url):
        return True
    html = ""
    try:
        html = (driver.page_source or "").lower()
    except Exception:
        pass
    form = [
        "login-form", "btn-login", 'id="login',
        'type="password"', "login with phone", "log in with",
    ]
    return any(ind in html for ind in form)


# ============================================================
# MAIN TEST
# ============================================================
def run_test():
    abs_profile = os.path.abspath(PROFILE_PATH)

    print("=" * 70)
    print("SHOPEE SCRAPER TESTER")
    print("=" * 70)
    print("PROFILE_PATH          :", PROFILE_PATH)
    print("ABSOLUTE PROFILE PATH :", abs_profile)
    print("PROFILE EXISTS        :", os.path.exists(abs_profile))
    print("AFFILIATE URL         :", AFFILIATE_URL)
    print("=" * 70)

    if not os.path.exists(abs_profile):
        print("\n[ERROR] Profile ./chromium TIDAK DITEMUKAN.")
        return 1

    driver = None
    try:
        # ------------------------------------------------------------
        # 1. BUAT DRIVER (persistent profile)
        # ------------------------------------------------------------
        print("\n[1] Membuat driver dengan create_driver(profile_path='./chromium') ...")
        driver = create_driver(profile_path=PROFILE_PATH)
        print("    Driver berhasil dibuat.")

        # ------------------------------------------------------------
        # 2. INJECT CAPTURE PDP API
        # ------------------------------------------------------------
        print("\n[2] Inject capture PDP API ...")
        injected = inject_pdp_capture(driver)
        print("    CDP injection :", "OK" if injected else "GAGAL (fallback DOM)")

        # ------------------------------------------------------------
        # 3. URL SEBELUM NAVIGASI
        # ------------------------------------------------------------
        try:
            before_url = driver.current_url
        except Exception:
            before_url = "(tidak bisa dibaca)"
        print("\n[3] CURRENT URL SEBELUM NAVIGASI :", before_url)

        # ------------------------------------------------------------
        # 4. BUKA AFFILIATE URL
        # ------------------------------------------------------------
        print("\n[4] Buka affiliate URL :", AFFILIATE_URL)
        try:
            driver.get(AFFILIATE_URL)
        except Exception as e:
            print("    [get error]", type(e).__name__, str(e)[:300])
            print("\n[E] TIMEOUT / GAGAL MEMBUKA URL")
            return 2

        # ------------------------------------------------------------
        # 5. TUNGGU REDIRECT
        # ------------------------------------------------------------
        print("\n[5] Menunggu redirect ...")
        start = time.time()
        final_url = driver.current_url or ""
        while "s.shopee.co.id" in final_url and (time.time() - start) < REDIRECT_TIMEOUT:
            time.sleep(1)
            try:
                final_url = driver.current_url or ""
            except Exception:
                break
        elapsed = time.time() - start
        print(f"    Redirect selesai dalam {elapsed:.1f}s")
        print("    CURRENT URL SETELAH NAVIGASI :", final_url)

        # ------------------------------------------------------------
        # 6. DETEKSI STATUS
        # ------------------------------------------------------------
        print("\n[6] Deteksi status halaman ...")

        if is_shopee_login_required(driver):
            print("\n[STATUS B] SHOPEE LOGIN REQUIRED")
            print("    Profile ./chromium tampaknya tidak memiliki session login")
            print("    atau session tidak dipakai oleh driver ini.")
            return 3

        if "s.shopee.co.id" in (final_url or ""):
            print("\n[STATUS C] REDIRECT GAGAL")
            return 4

        # ------------------------------------------------------------
        # 7. TUNGGU DATA PRODUK (SSR JSON / PDP API / DOM)
        # ------------------------------------------------------------
        print("\n[7] Menunggu data produk muncul ...")
        html = driver.page_source or ""
        start = time.time()
        while (
            "itemid" not in html
            and "item_id" not in html
            and not get_captured_pdp(driver)
            and (time.time() - start) < DATA_TIMEOUT
        ):
            time.sleep(1)
            try:
                html = driver.page_source or ""
            except Exception:
                break
        time.sleep(SETTLE_TIME)
        html = driver.page_source or ""

        try:
            with open(DEBUG_HTML_FILE, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"    Page source disimpan ke : {DEBUG_HTML_FILE} ({len(html)} bytes)")
        except Exception as e:
            print("    [gagal simpan html]", e)

        # ------------------------------------------------------------
        # 8. EKSTRAKSI METADATA (bertingkat)
        # ------------------------------------------------------------
        print("\n[8] Ekstraksi metadata ...")
        meta = {}

        # 8a. PDP API (sumber terbaik)
        pdp = get_captured_pdp(driver)
        if pdp:
            meta = extract_from_pdp(pdp)
            print("    Sumber utama  : PDP API (/api/v4/pdp/get_pc)")
        else:
            print("    Sumber utama  : URL + SSR HTML + DOM (PDP API tidak tertangkap)")

        # 8b. URL hasil redirect
        meta = extract_from_url(final_url, meta)

        # 8c. SSR HTML / title tag
        meta = extract_from_html(html, meta)

        # 8d. Rendered DOM (innerText)
        try:
            inner_text = driver.execute_script("return document.body.innerText;") or ""
        except Exception:
            inner_text = ""
        meta = extract_from_dom(inner_text, meta)

        # ------------------------------------------------------------
        # 9. PRINT HASIL
        # ------------------------------------------------------------
        title_tag = re.search(r"<title>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
        print("\n    PAGE TITLE :", (title_tag.group(1).strip() if title_tag else "(kosong)"))

        print("\n" + "=" * 70)
        print("HASIL METADATA")
        print("=" * 70)
        print(f"FINAL URL     : {final_url}")
        print(f"PRODUCT ID    : {meta.get('product_id')}")
        print(f"SHOP ID       : {meta.get('shop_id')}")
        print(f"TITLE         : {meta.get('title')}")
        print(f"DESCRIPTION   : {(meta.get('description') or '')[:120]}")
        print(f"PRICE         : {meta.get('price')}")
        print(f"SOLD          : {meta.get('sold_count')}")
        print(f"RATING        : {meta.get('rating')}")
        print(f"REVIEW COUNT  : {meta.get('review_count')}")
        print(f"SHOP NAME     : {meta.get('shop_name')}")
        print(f"SHOP LOCATION : {meta.get('shop_location')}")
        print("=" * 70)

        for key in ["product_id", "shop_id", "title", "price", "sold_count", "rating", "review_count"]:
            if meta.get(key) is None:
                print(f"  [INFO] {key} = None (tidak ditemukan di halaman)")

        # ------------------------------------------------------------
        # 10. KRITERIA MINIMAL
        # ------------------------------------------------------------
        ok = (
            meta.get("product_id") is not None
            and meta.get("shop_id") is not None
            and meta.get("title") is not None
            and meta.get("price") is not None
        )
        print("\n[STATUS A] PRODUK BERHASIL DIBUKA" if ok else "\n[STATUS E] METADATA MINIMAL BELUM LENGKAP")
        print("    Minimal product_id, shop_id, title, price :", "OK" if ok else "BELUM")
        print("    (extra: sold/rating/review_count jika tersedia)")
        return 0 if ok else 6

    except Exception as e:
        print("\n[ERROR] Exception tidak terduga :", type(e).__name__, str(e)[:500])
        return 7
    finally:
        if driver is not None:
            try:
                driver.quit()
                print("\nDriver ditutup.")
            except Exception:
                pass


if __name__ == "__main__":
    code = run_test()
    print(f"\nExit code: {code}")
    sys.exit(code)
