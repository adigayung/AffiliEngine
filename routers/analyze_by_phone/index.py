from flask import Blueprint, request, jsonify
from PIL import Image
import os
import re

from includes.product_analyzer import analyze_product
from includes.logFX import logger

analyze_by_phone_bp = Blueprint(
    "analyze_by_phone_bp",
    __name__,
    url_prefix="/api"
)

def extract_url(text: str) -> str | None:
    """
    Mengambil URL dari string dan mengembalikan hanya URL-nya.
    Jika tidak ada URL, return None.
    """

    pattern = r"(https?://[^\s]+)"
    match = re.search(pattern, text)

    if match:
        return match.group(1)

    return None

@analyze_by_phone_bp.route("/analyze-by-phone", methods=["POST"])
def analyze_by_phone():
    print("ok request masuk")

    # ambil file
    try:
        image = request.files.get("image")
        print("image beres", flush=True)
    except Exception as e:
        print("ERROR:", repr(e), flush=True)
        raise
    # ambil url
    url = extract_url(request.form.get("url"))
    print("url beres")
    if image:
        save_dir = "./upload"
        os.makedirs(save_dir, exist_ok=True)

        filename = os.path.splitext(image.filename)[0]  # tanpa ekstensi
        save_path = os.path.join(save_dir, f"{filename}.jpg")

        # buka image dari stream
        img = Image.open(image.stream)

        # convert ke RGB (penting biar PNG transparan tidak error)
        img = img.convert("RGB")

        # save sebagai JPG
        img.save(save_path, "JPEG", quality=95)

        print("image saved:", save_path)
        print("url:", url)
        logger(
            "info",
            "Memulai Analize..."
        )
        result = analyze_product(
            image=save_path,
            product_link=url,
            enable_llm=True
        )
        logger(
            "info",
            "Analize Selesai..."
        )
    return jsonify({
        "status": "success",
        "message": "received",
        "file": image.filename if image else None,
        "url": url
    })