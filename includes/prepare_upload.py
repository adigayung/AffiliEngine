# File : includes/prepare_upload.py

from includes.mysql import get_product

def generate_prepare_upload(product_list):

    hasil = []

    for product_id in product_list:

        product = get_product(product_id)

        if product:
            hasil.append(product)

    return hasil