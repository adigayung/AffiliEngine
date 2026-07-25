from flask import Blueprint, render_template, request
from datetime import datetime
from includes.mysql import get_all_products

from includes.product_analyzer import analyze_product

product_rating_bp = Blueprint(
    "product_rating",
    __name__,
    url_prefix="/product-rating"
)

@product_rating_bp.route("/")
def index():
    return render_template(
        "product_rating/index.html",
        page_title="Product Rating"
    )

@product_rating_bp.route("/analyze", methods=["POST"])
def analyze():

    products = get_all_products()

    result = analyze_product(
        image=request.files["image"],
        product_link=request.form.get("product_link"),
        enable_llm=True
    )

    return render_template(
        "product_rating/index.html",
        text=result["product"],
        analysis=result["analysis"],
        hasil_llm=result["hasil_llm"],
        products=products
    )