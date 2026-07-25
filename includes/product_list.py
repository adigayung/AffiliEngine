from includes.logFX import logger
from includes.mysql import (
get_product_analysis,
get_llm_analysis,
get_all_products
)

def get_product_list():

    products = get_all_products()

    for product in products:

        product["product_analysis"] = get_product_analysis(product["id"])
        product["llm_analysis"] = get_llm_analysis(product["id"])
        #logger("info", f"isi : {product}")

    return products