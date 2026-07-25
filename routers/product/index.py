# File : routers\product\index.py
from flask import Blueprint, render_template, session

from includes.product_list  import get_product_list
from includes.logFX import logger
from includes.mysql import get_product
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
    return render_template(
        "product/index.html",
        product=product
    )