# File includes\compare_products.py
import os
import json
import ast
import re
from flask import jsonify
from includes.utils import mapping_untuk_llm
from includes.prepare_upload  import generate_prepare_upload
from includes.config_loader import get_app_config, get_openrouter_config
from includes.openrouter import LLM_OpenRouter
from includes.logFX import logger
from includes.mysql import get_product_basic

def apply_weight_ai(
    ai_result,
    total_video
):

    if not ai_result:

        return {}

    total_weight = sum(
        item.get("weight",0)
        for item in ai_result.values()
    )

    if total_weight <= 0:

        return {}

    result = {}

    remain = []

    allocated = 0


    for product_id,item in ai_result.items():

        exact = (
            item["weight"]
            /
            total_weight
        ) * total_video


        qty = int(exact)

        result[product_id] = qty

        allocated += qty


        remain.append({

            "product_id": product_id,

            "priority": item.get(
                "priority",
                999
            )

        })


    remaining = total_video - allocated


    remain.sort(
        key=lambda x:x["priority"]
    )


    if remain:

        index = 0

        while remaining > 0:

            product_id = remain[index]["product_id"]

            result[product_id] += 1

            remaining -= 1

            index += 1

            if index >= len(remain):

                index = 0

    return result

def parse_llm_json(text):

    if isinstance(text, dict):
        return text

    if not isinstance(text, str):
        raise TypeError(f"Unexpected type: {type(text)}")

    text = text.strip()

    # Hilangkan markdown
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text)
    text = text.strip()

    # Coba JSON asli
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Coba Python dict
    try:
        return ast.literal_eval(text)
    except Exception:
        pass

    raise ValueError(f"Invalid LLM JSON:\n{text}")

def bandingkan(products):
    # memnadingkan product
    # products = ['1732299219062326776', '1735091848673724357', '1735679989189543360']
    produk_input = ""
    openrouter_config = get_openrouter_config()
    app_config = get_app_config()
    prompt_file = os.path.join(
        "prompt",
        "analisa_compare.txt"
    )

    with open(
        prompt_file,
        "r",
        encoding="utf-8"
    ) as f:

        prompt_llm = f.read()

    
    data_products = generate_prepare_upload(products)
    string_untuk_llm = mapping_untuk_llm(data_products)

    for i, produk in enumerate(string_untuk_llm, start=1):

        positive_review = (
            "Unknown"
            if not produk["positive_review"]
            else f"{produk['positive_review']}%"
        )

        produk_input += "=" * 40 + "\n"
        produk_input += f"PRODUK #{i}\n"
        produk_input += "=" * 40 + "\n\n"

        produk_input += f"Product ID          : {produk['product_id']}\n"
        produk_input += f"Title               : {produk['title']}\n\n"

        produk_input += f"Opportunity Score   : {produk['opportunity_score']:.2f} / 100\n"
        produk_input += f"Rating              : {produk['rating']}\n\n"

        produk_input += f"Lifetime Sold       : {produk['sold']:,}\n"
        produk_input += f"Commission          : Rp {produk['commission']:,} / sale\n"
        produk_input += f"Product Price       : Rp {produk['price']:,}\n\n"

        produk_input += f"Affiliate Creators  : {produk['creator_count']:,}\n"
        produk_input += f"CTR                 : {float(produk['ctr']):.2f}%\n"
        produk_input += f"Positive Review     : {positive_review}\n"
        produk_input += f"Available Stock     : {produk['stock']:,}\n"
        produk_input += f"Trend               : {produk['trend']}\n\n"


    prompt_string = prompt_llm.replace(
        "[[#PRODUCTS_DATA]]",
        produk_input
    )
    hasil_llm = LLM_OpenRouter(
        openrouter_config["models"]["compare_products"],
        openrouter_config["api_key"],
        prompt_string,
        api_url=openrouter_config["base_url"],
        site_title=app_config["app_name"].replace(
            " ",
            "-"
        )
    )

    hasil = parse_llm_json(hasil_llm)

    for product_id in hasil:

        product = get_product_basic(product_id)

        if product:

            hasil[product_id]["title"] = product["title"]
            hasil[product_id]["image"] = f'/static/products/{product["tiktok_id_product"]}/product/1.jpg'

    return hasil