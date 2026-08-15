"""
Validator URL affiliate Shopee.

Format yang DITERIMA (wajib):
    https://s.shopee.co.id/<affiliate_code>

Contoh valid:
    https://s.shopee.co.id/50YEc82zhI

Format yang DITOLAK:
    - http://s.shopee.co.id/...
    - https://shopee.co.id/...
    - https://www.shopee.co.id/...
    - https://s.shopee.co.id.evil.com/...   (domain menyamar)
    - URL kosong / tanpa kode affiliate / malformed
"""

import re
from urllib.parse import urlparse

# Hostname yang diizinkan (exact match)
ALLOWED_HOSTNAME = "s.shopee.co.id"

# Kode affiliate: alfanumerik tanpa karakter khusus
AFFILIATE_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]+$")


def is_valid_affiliate_url(raw_url):
    """
    Validasi ketat Shopee Affiliate URL.

    Menggunakan urlparse + regex (bukan startswith), sehingga
    domain menyamar seperti `s.shopee.co.id.evil.com` ditolak.

    Returns:
        bool: True jika URL valid
    """
    if not raw_url or not isinstance(raw_url, str):
        return False

    url = raw_url.strip()
    if not url:
        return False

    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    # Scheme WAJIB https
    if parsed.scheme != "https":
        return False

    # Hostname harus exact `s.shopee.co.id`
    if parsed.hostname != ALLOWED_HOSTNAME:
        return False

    # Tolak credential / port aneh pada netloc
    if parsed.username or parsed.password:
        return False
    if parsed.port not in (None, 443):
        return False

    # Path harus berisi satu segmen kode affiliate
    path = parsed.path or ""
    if not path.startswith("/"):
        return False

    code = path[1:]
    if not code or "/" in code or not AFFILIATE_CODE_PATTERN.match(code):
        return False

    # Format standar tidak boleh ada query / fragment
    if parsed.query or parsed.fragment:
        return False

    return True
