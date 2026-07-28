"""
Product Momentum Module.

Module untuk menganalisis momentum produk berdasarkan data video TikTok.
Menggunakan algoritma yang telah divalidasi dari hitung.py.

Alur:
1. collect_data()       - Ambil data dari database via mysql.py
2. calculate_momentum() - Hitung momentum score per produk
3. calculate_discovery()- Hitung discovery score per produk
4. classify()          - Klasifikasikan status produk
5. build_summary()     - Buat ringkasan statistik
6. build_chart_data()  - Siapkan data untuk grafik
"""

from .analyzer import ProductMomentumAnalyzer, analyze_product_momentum

__all__ = [
    "ProductMomentumAnalyzer",
    "analyze_product_momentum",
]
