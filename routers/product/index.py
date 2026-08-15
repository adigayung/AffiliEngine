# File : routers\product\index.py
from flask import Blueprint, render_template, session, request, jsonify

from includes.product_list  import get_product_list
from includes.logFX import logger
from includes.mysql import get_product
from includes.product.shopee.db import get_shopee_products_for_tiktok
from includes.product.shopee.service import (
    add_shopee_product,
    remove_shopee_product
)
product_ID_bp = Blueprint(
    "product",
    __name__,
    url_prefix="/product"
)


@product_ID_bp.route("/<string:product_id>")
def product_detail(product_id):

    product = get_product(product_id)
     #logger("debug", f"isi : {product}")
    # if not product:
    #     abort(404)
    print ("session : ", session["creator_id"])

    # Shopee Affiliate Products yang terhubung dengan TikTok Product ini
    shopee_products = []

    if product:
        shopee_products = get_shopee_products_for_tiktok(product_id)

    return render_template(
        "product/index.html",
        product=product,
        shopee_products=shopee_products
    )


@product_ID_bp.route("/<string:product_id>/shopee/add", methods=["POST"])
def shopee_add(product_id):
    """
    Tambah Shopee Affiliate Product untuk TikTok Product.
    Request body: affiliate_url (form).
    """
    affiliate_url = request.form.get("affiliate_url", "")

    result = add_shopee_product(product_id, affiliate_url)

    return jsonify(result)


@product_ID_bp.route(
    "/<string:product_id>/shopee/remove/<string:shopee_product_id>",
    methods=["POST"]
)
def shopee_remove(product_id, shopee_product_id):
    """
    Hapus relasi TikTok Product <-> Shopee Product.
    """
    result = remove_shopee_product(product_id, shopee_product_id)

    return jsonify(result)
