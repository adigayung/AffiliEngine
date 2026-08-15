"""
Shopee Affiliate Product Module.

Module untuk mengelola Shopee Affiliate Product yang terhubung
dengan TikTok Product pada halaman /product/<tiktok_product_id>.

Folder ini berisi:
    validator.py - Validasi Shopee Affiliate URL
    scraper.py   - Ambil metadata Shopee via existing Chromium driver
    db.py        - Database operations (shopee_products, tiktok_shopee_products)
    service.py   - Orchestration layer (alur bisnis add/remove)
"""
