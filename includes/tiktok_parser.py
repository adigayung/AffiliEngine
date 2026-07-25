import json
import re
from includes.config_loader import get_openrouter_config
from includes.openrouter import LLM_OpenRouter

config = get_openrouter_config()

# =========================
# CONFIG
# =========================
base_url = config["base_url"]
OPENROUTER_API_KEY = config["api_key"]

VISION_MODEL = config["models"]["image_analysis"]
text_model = config["models"]["text_analysis"]

# =========================
# PROMPT
# =========================

PROMPT_TIKTOK_ANALYTICS = """
Analisa gambar screenshot TikTok affiliate analytics.

Extract data berikut dari gambar:

- komisi
- stok_tersedia
- ulasan_positif
- pesanan
- ctr
- jumlah_kreator
- pembeli_keranjang

Rules:
- Return JSON ONLY
- Tanpa markdown
- Tanpa penjelasan
- Tanpa ```json
- Convert K menjadi angka penuh
- 89.2K => 89200
- 3,3K => 3300
- 1,3K => 1300
- Jangan sampai salah menulai, misal 4,0K hasilnya kamu tulis 4000 bukan 40
- 85% => 85
- ctr harus float
- Semua angka tanpa simbol %

Format wajib:

{
  "komisi": 680,
  "stok_tersedia": 89200,
  "ulasan_positif": 85,
  "pesanan": 3300,
  "ctr": 5.2,
  "jumlah_kreator": 156,
  "pembeli_keranjang": 1300
}
"""

# =========================
# PARSER
# =========================

def parse_tiktok_analytics(image_path):

    result = LLM_OpenRouter(
        model=VISION_MODEL,
        apikey=OPENROUTER_API_KEY,
        api_url=base_url,
        imgPath=image_path,
        prompt=PROMPT_TIKTOK_ANALYTICS,
        single=True
    )
    print("result : ", result)
    try:

        # bersihkan markdown kalau ada
        cleaned = result.strip()

        cleaned = cleaned.replace(
            "```json",
            ""
        )

        cleaned = cleaned.replace(
            "```",
            ""
        )

        cleaned = cleaned.strip()

        parsed_json = json.loads(cleaned)

        return parsed_json

    except Exception as e:

        return {
            "error": str(e),
            "raw_result": result
        }