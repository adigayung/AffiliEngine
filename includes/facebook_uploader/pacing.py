"""
pacing.py — Randomized human-like pacing.

Behavior IDENTIK dengan main.py golden version:
- random.uniform()
- tanpa random seed tetap
- tanpa dependency tambahan
- hanya lapisan pacing; bukan pengganti explicit wait.
"""

import random
import time

# Range delay per kategori (min, max) dalam detik.
DELAY_MICRO = (0.2, 0.6)         # interaksi ringan
DELAY_NORMAL = (0.4, 1.2)        # sebelum/sesudah klik tombol
DELAY_TRANSITION = (0.8, 2.0)    # setelah aksi yang mengubah UI/dialog
DELAY_MAJOR = (1.0, 3.0)         # perpindahan tahap besar


def human_delay(category, label=None):
    """
    Jeda acak seragam [min, max] dari kategori tertentu.

    - category : salah satu tuple range (DELAY_MICRO, DELAY_NORMAL, ...).
    - label    : jika diisi, jeda di-log untuk audit (hanya action penting).

    Bukan pengganti WebDriverWait; dipanggil di sela-sela explicit wait.
    Mengembalikan durasi aktual (detik) agar bisa di-log/diinspeksi.
    """
    low, high = category
    duration = random.uniform(low, high)
    time.sleep(duration)
    if label:
        print(f"[INFO] Human pacing {label}: {duration:.2f}s")
    return duration
