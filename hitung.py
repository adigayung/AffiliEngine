import math
import statistics
import random


# ================================================================
# GENERATE DUMMY DATA - REALISTIC LARGE DATASET
# ================================================================
# Menghasilkan 50 produk, ~300-500 video, 100 creator, 30 hari
# ================================================================

def generate_dummy_data():
    """Menghasilkan dataset dummy realistis untuk menguji algoritma."""
    random.seed(42)  # Reproducible

    creator_pool = [f"Creator_{i}" for i in range(100)]
    video_counter = [0]

    def next_vid():
        video_counter[0] += 1
        return f"V{video_counter[0]:04d}"

    def pick_creators(n):
        return random.sample(creator_pool, min(n, len(creator_pool)))

    def noise(val):
        return int(val * random.uniform(0.85, 1.15))

    def views_growth(start, end, days=30, power=2.0):
        """Growth curve: slow start, accelerating."""
        v = []
        for d in range(days):
            p = d / max(days - 1, 1)
            base = start + (end - start) * (p ** power)
            v.append(max(0, noise(base)))
        return v

    def views_linear(start, daily_inc, days=30):
        """Linear daily increase."""
        v = []
        for d in range(days):
            base = start + daily_inc * d
            v.append(max(100, noise(base)))
        return v

    def views_spike(days=30):
        """Flat then sudden explosion."""
        v = []
        for d in range(days):
            if d < 20:
                base = random.uniform(0, 500)
            elif d < 24:
                base = random.uniform(500, 8000)
            elif d < 27:
                progress = (d - 23) / 3
                base = 8000 + progress * 500000
            else:
                progress = (d - 26) / 4
                base = 500000 + progress * 2500000
            v.append(max(0, noise(base)))
        return v

    def views_old_viral(days=30):
        """Fast growth then plateau."""
        v = []
        for d in range(days):
            if d < 8:
                base = 50000 + d * 60000
            elif d < 18:
                base = 530000 + (d - 8) * 35000
            elif d < 25:
                base = 880000 + (d - 18) * 10000
            else:
                base = 950000 + (d - 25) * 2000
            v.append(max(0, noise(base)))
        return v

    def views_noise_walk(days=30):
        """Random walk terbatas - naik turun dalam range wajar."""
        v = []
        trend = random.choice([-1, 1])
        change_counter = random.randint(3, 7)
        for d in range(days):
            if d == 0:
                base = random.uniform(5000, 50000)
            else:
                change_counter -= 1
                if change_counter <= 0:
                    trend = random.choice([-1, 1])
                    change_counter = random.randint(3, 7)
                jump = trend * random.uniform(0.05, 0.25)
                base = v[-1] * (1 + jump)
            base = max(3000, min(base, 500000))
            v.append(max(1000, noise(base)))
        return v

    data = []

    # ============================================================
    # 1. TRUE WINNER (5 produk) — Target: Momentum TOP 5
    # ============================================================
    # 15-30 video, 10-20 creator, growth konsisten naik
    for name in ["Premium Dress", "Viral Beauty Serum", "Korean Bag",
                  "Elegant Shoes", "Daily Outfit"]:
        n_vid = random.randint(15, 30)
        creators = pick_creators(random.randint(10, 20))
        for _ in range(n_vid):
            c = random.choice(creators)
            s = random.randint(500, 2000)
            e = random.randint(200000, 800000)
            p = random.uniform(1.5, 2.5)
            data.append({
                "product": name, "video_id": next_vid(),
                "creator": c, "daily_views": views_growth(s, e, power=p)
            })

    # ============================================================
    # 2. VIRAL SPIKE (5 produk) — Target: DISCOVERY TOP
    # ============================================================
    # 1-2 video, 1 creator, tiba-tiba meledak
    for name in ["New TikTok Find", "Unknown Product", "Sudden Viral",
                  "Mystery Item", "Flash Trend"]:
        n_vid = random.choices([1, 2], weights=[0.7, 0.3])[0]
        c = random.choice(creator_pool)
        for _ in range(n_vid):
            data.append({
                "product": name, "video_id": next_vid(),
                "creator": c, "daily_views": views_spike()
            })

    # ============================================================
    # 3. OLD VIRAL (5 produk) — Momentum HARUS TURUN
    # ============================================================
    # Banyak video/creator, total views besar, growth berhenti
    for name in ["Old Fashion Trend", "Former Viral Dress", "Last Year Hit",
                  "Classic Jacket", "Timeless Heels"]:
        n_vid = random.randint(10, 20)
        creators = pick_creators(random.randint(5, 10))
        for _ in range(n_vid):
            c = random.choice(creators)
            data.append({
                "product": name, "video_id": next_vid(),
                "creator": c, "daily_views": views_old_viral()
            })

    # ============================================================
    # 4. STABLE SLOW WINNER (5 produk) — Momentum CUKUP TINGGI
    # ============================================================
    # Banyak video/creator, growth kecil tapi stabil
    for name in ["Basic Tee", "Comfort Pants", "Everyday Skincare",
                  "Home Decor Set", "Kitchen Tool"]:
        n_vid = random.randint(10, 15)
        creators = pick_creators(random.randint(5, 10))
        for _ in range(n_vid):
            c = random.choice(creators)
            s = random.randint(5000, 20000)
            d = random.randint(5000, 15000)
            data.append({
                "product": name, "video_id": next_vid(),
                "creator": c, "daily_views": views_linear(s, d)
            })

    # ============================================================
    # 5. FAKE TREND / NOISE (10 produk) — Score HARUS RENDAH
    # ============================================================
    # Growth random naik-turun, consistency & stability rendah
    for name in [f"Fake Trend {i}" for i in range(1, 11)]:
        n_vid = random.randint(3, 8)
        creators = pick_creators(random.randint(2, 5))
        for _ in range(n_vid):
            c = random.choice(creators)
            data.append({
                "product": name, "video_id": next_vid(),
                "creator": c, "daily_views": views_noise_walk()
            })

    # ============================================================
    # 6. SINGLE VIDEO VIRAL (5 produk) — Discovery TINGGI, Momentum RENDAH
    # ============================================================
    # 1 video, views besar (5jt+), kena penalty berat
    for name in ["One Hit Wonder", "Single Viral Clip", "Mega View Item",
                  "Trending Solo", "Viral Reel"]:
        c = random.choice(creator_pool)
        s = random.randint(1000, 10000)
        e = random.randint(3000000, 8000000)
        data.append({
            "product": name, "video_id": next_vid(),
            "creator": c, "daily_views": views_growth(s, e, power=3.0)
        })

    # ============================================================
    # 7. NORMAL PRODUCT (15 produk) — Pengisi
    # ============================================================
    for i in range(1, 16):
        name = f"Normal Product {i}"
        n_vid = random.randint(3, 6)
        creators = pick_creators(random.randint(2, 4))
        for _ in range(n_vid):
            c = random.choice(creators)
            s = random.randint(200, 5000)
            e = random.randint(10000, 200000)
            p = random.uniform(1.2, 2.8)
            data.append({
                "product": name, "video_id": next_vid(),
                "creator": c, "daily_views": views_growth(s, e, power=p)
            })

    return data


data = generate_dummy_data()


def hitung_daily_growth(daily_views):
    """Menghitung array growth harian dari data views."""
    growths = []
    for i in range(1, len(daily_views)):
        growth = daily_views[i] - daily_views[i - 1]
        growths.append(growth)
    return growths


# ================================================================
# TAHAP 2: TERAPKAN RECENCY WEIGHT (Bobot Hari Terbaru)
# ================================================================
# Growth hari ke-8  (index 6) -> bobot 0.2
# Growth hari ke-9  (index 7) -> bobot 0.3
# Growth hari ke-10 (index 8) -> bobot 0.5
#
# Untuk data 10 hari -> 9 growth period.
# Bobot hanya untuk 3 hari terakhir; hari-hari sebelumnya bobot = 0.
# ================================================================

def hitung_weighted_growth(growths):
    """Menghitung weighted growth dengan bobot recency."""
    weights = [0.0] * len(growths)

    # Beri bobot hanya untuk 3 growth terakhir
    if len(growths) >= 3:
        weights[-3] = 0.2   # growth day8
        weights[-2] = 0.3   # growth day9
        weights[-1] = 0.5   # growth day10
    elif len(growths) == 2:
        weights[-2] = 0.4
        weights[-1] = 0.6
    elif len(growths) == 1:
        weights[-1] = 1.0

    total = 0.0
    for i in range(len(growths)):
        total += growths[i] * weights[i]

    return total


# ================================================================
# TAHAP 3: HITUNG CONSISTENCY
# ================================================================
# Consistency = proporsi hari-hari dengan growth positif.
# Semakin konsisten produk tumbuh setiap hari, semakin tinggi skor.
# ================================================================

def hitung_konsistensi(growths):
    """Menghitung rasio growth positif terhadap total growth period."""
    if len(growths) == 0:
        return 0.0
    positif = sum(1 for g in growths if g > 0)
    return positif / len(growths)


# ================================================================
# PROSES SEMUA DATA
# ================================================================

produk_data = {}  # key: nama produk

for item in data:
    product_name = item["product"]
    video_id = item["video_id"]
    creator = item["creator"]
    views = item["daily_views"]

    # Hitung daily growth
    growths = hitung_daily_growth(views)

    # Hitung weighted growth (dengan recency weight)
    weighted_growth = hitung_weighted_growth(growths)

    # Hitung konsistensi
    konsistensi = hitung_konsistensi(growths)

    video_info = {
        "video_id": video_id,
        "creator": creator,
        "weighted_growth": weighted_growth,
        "konsistensi": konsistensi,
    }

    if product_name not in produk_data:
        produk_data[product_name] = {
            "videos": [],
            "creators": set(),
        }

    produk_data[product_name]["videos"].append(video_info)
    produk_data[product_name]["creators"].add(creator)



# ================================================================
# TAHAP 4: HITUNG METRIK PER PRODUK
# ================================================================

hasil = []

for product_name, pdata in produk_data.items():
    videos = pdata["videos"]
    creators = pdata["creators"]

    video_count = len(videos)
    creator_count = len(creators)

    # --- A. Average Video Growth ---
    # Total weighted growth semua video dibagi jumlah video
    total_weighted_growth = sum(v["weighted_growth"] for v in videos)
    avg_weighted_growth = total_weighted_growth / video_count if video_count > 0 else 0

    # --- B. Video Validation (Confidence) ---
    # Semakin banyak video, semakin dipercaya
    # Rumus: min(video_count / 5, 1)
    confidence = min(video_count / 5.0, 1.0)

    # ============================================================
    # PERBAIKAN 2: Creator Factor (Logarithmic)
    # ============================================================
    # Sebelumnya: min(creator_count / 5, 1)  → linear
    # Sekarang:   min(log(creator_count+1) / log(6), 1)
    #
    # Alasan:
    # 1 creator ke 2 creator sangat berarti.
    # 10 creator ke 11 creator tidak terlalu berarti.
    #
    # Hasil:
    # 1 creator ≈ 0.38
    # 2 creator ≈ 0.61
    # 3 creator ≈ 0.77
    # 5 creator = 1.0
    # ============================================================
    if creator_count > 0:
        creator_factor = min(
            math.log(creator_count + 1) / math.log(6),
            1.0
        )
    else:
        creator_factor = 0.0

    # --- C. Consistency ---
    # Rata-rata konsistensi dari semua video di produk ini
    avg_konsistensi = sum(v["konsistensi"] for v in videos) / video_count if video_count > 0 else 0

    # ============================================================
    # PERBAIKAN 3: Growth Distribution / Stability
    # ============================================================
    # Mengukur seberapa merata growth antar video.
    # Produk dengan distribusi growth sehat (semua video naik)
    # mendapat bonus.
    # Produk dengan 1 video sukses dan lainnya 0 akan kena penalty.
    #
    # Rumus: stability = 1 / (1 + growth_std / 100000)
    # Jika hanya 1 video: growth_std = 0 → stability = 1.0
    # ============================================================
    growth_values = [v["weighted_growth"] for v in videos]

    if video_count > 1:
        growth_std = statistics.stdev(growth_values)
    else:
        growth_std = 0

    stability = 1.0 / (1.0 + growth_std / 100000.0)

    # --- D. Single Viral Penalty ---
    # Jika hanya 1 video, kena penalti besar
    if video_count == 1:
        penalty = 0.25
    elif video_count == 2:
        penalty = 0.50
    else:  # video_count >= 3
        penalty = 1.0

    # ============================================================
    # PERBAIKAN 1: Growth Score dengan Exposure Factor
    # ============================================================
    # Sebelumnya: growth_score = sqrt(avg_weighted_growth)
    #
    # Masalah: Produk dengan 1 video viral masih terlalu kuat.
    # Contoh:
    #   Produk A: 100 video, growth rata-rata 10.000
    #   Produk B: 1 video, growth 1.000.000
    # Produk B tidak boleh otomatis menang.
    #
    # Perbaikan: Tambahkan exposure_factor = log(video_count + 1)
    # Semakin banyak video yang membuktikan produk,
    # semakin kuat growth tersebut.
    #
    # Rumus baru:
    #   growth_score = sqrt(avg_weighted_growth) * exposure_factor
    # ============================================================
    exposure_factor = math.log(video_count + 1)

    safe_growth = max(avg_weighted_growth, 0)
    growth_score = math.sqrt(safe_growth) * exposure_factor

    # ============================================================
    # PERBAIKAN FORMULA: Momentum Score
    # ============================================================
    # Formula baru dengan stability:
    #
    # momentum_score = (
    #     growth_score * 0.45
    #     + confidence * 100 * 0.20
    #     + creator_factor * 100 * 0.15
    #     + avg_konsistensi * 100 * 0.10
    #     + stability * 100 * 0.10
    # ) * penalty
    # ============================================================
    momentum_score = (
        growth_score * 0.45
        + confidence * 100 * 0.20
        + creator_factor * 100 * 0.15
        + avg_konsistensi * 100 * 0.10
        + stability * 100 * 0.10
    )

    # Terapkan penalty untuk single video
    momentum_score = momentum_score * penalty

    # ============================================================
    # PERBAIKAN 4: Discovery Score
    # ============================================================
    # Sebelumnya: discovery_score = growth_score * (1 - confidence)
    #
    # Masalah: Masih terlalu mudah dimenangkan oleh spike.
    #
    # Perbaikan: Tambahkan faktor konsistensi.
    #
    # Rumus baru:
    #   discovery_score = growth_score
    #                     * (1 - confidence)
    #                     * (0.5 + avg_konsistensi)
    #
    # Tujuan:
    # Produk baru tetap ditemukan,
    # tetapi produk dengan growth yang lebih konsisten
    # lebih dipercaya.
    # ============================================================
    discovery_score = (
        growth_score
        * (1 - confidence)
        * (0.5 + avg_konsistensi)
    )

    hasil.append({
        "product": product_name,
        "momentum_score": round(momentum_score, 2),
        "discovery_score": round(discovery_score, 2),
        "avg_growth": round(avg_weighted_growth),
        "videos": video_count,
        "creators": creator_count,
        "confidence": round(confidence, 2),
        "creator_factor": round(creator_factor, 2),
        "consistency": round(avg_konsistensi, 2),
        "stability": round(stability, 3),
        "exposure_factor": round(exposure_factor, 3),
        "penalty": penalty,
        "growth_score": round(growth_score, 2),
    })


# ================================================================
# OUTPUT: PRODUCT MOMENTUM (TOP 20)
# ================================================================
# Ranking berdasarkan momentum_score (tertinggi pertama)
# ================================================================

momentum_rank = sorted(hasil, key=lambda x: x["momentum_score"], reverse=True)

# --- Statistik Dataset ---
total_videos = sum(len(pd["videos"]) for pd in produk_data.values())
total_products = len(produk_data)
total_creators = len(set(c for pd in produk_data.values() for c in pd["creators"]))

print("=" * 60)
print("  DATASET STATISTICS")
print("=" * 60)
print(f"  Products : {total_products}")
print(f"  Videos   : {total_videos}")
print(f"  Creators : {total_creators}")
print(f"  Days     : 30")
print("=" * 60)

print("\n" + "=" * 60)
print("  PRODUCT MOMENTUM - TOP 20")
print("=" * 60)

for i, item in enumerate(momentum_rank[:20], 1):
    print(f"""
  #{i} {item['product']}
  ----------------------
  Momentum Score   : {item['momentum_score']}
  Discovery Score  : {item['discovery_score']}
  Growth Score     : {item['growth_score']}
  Avg Growth       : {item['avg_growth']:,}
  Videos           : {item['videos']}
  Creators         : {item['creators']}
  Confidence       : {item['confidence']}
  Creator Factor   : {item['creator_factor']}
  Consistency      : {item['consistency']}
  Stability        : {item['stability']}
  Exposure Factor  : {item['exposure_factor']}
  Penalty          : {item['penalty']}
  ----------------------
""")


# ================================================================
# OUTPUT: DISCOVERY RADAR (TOP 20)
# ================================================================
# Ranking berdasarkan discovery_score (tertinggi pertama)
# ================================================================

discovery_rank = sorted(hasil, key=lambda x: x["discovery_score"], reverse=True)

print("=" * 60)
print("  DISCOVERY RADAR - TOP 20")
print("=" * 60)

for i, item in enumerate(discovery_rank[:20], 1):
    print(f"""
  #{i} {item['product']}
  ----------------------
  Discovery Score  : {item['discovery_score']}
  Momentum Score   : {item['momentum_score']}
  Growth Score     : {item['growth_score']}
  Avg Growth       : {item['avg_growth']:,}
  Videos           : {item['videos']}
  Creators         : {item['creators']}
  Confidence       : {item['confidence']}
  Consistency      : {item['consistency']}
  Stability        : {item['stability']}
  Exposure Factor  : {item['exposure_factor']}
  ----------------------
""")


# ================================================================
# RINGKASAN SINGKAT
# ================================================================

print("=" * 60)
print("  RINGKASAN RANKING (TOP 20)")
print("=" * 60)

print("\n  ** MOMENTUM:")
for i, item in enumerate(momentum_rank[:20], 1):
    tag = ""
    if "Premium" in item["product"] or "Viral Beauty" in item["product"] or "Korean" in item["product"] or "Elegant" in item["product"] or "Daily Outfit" in item["product"]:
        tag = " [WINNER]"
    elif "Spike" in item["product"] or "TikTok" in item["product"] or "Unknown" in item["product"] or "Sudden" in item["product"] or "Mystery" in item["product"] or "Flash" in item["product"]:
        tag = " [SPIKE]"
    elif "Old" in item["product"] or "Former" in item["product"] or "Last Year" in item["product"] or "Classic" in item["product"] or "Timeless" in item["product"]:
        tag = " [OLD]"
    elif "Fake" in item["product"]:
        tag = " [NOISE]"
    elif "One Hit" in item["product"] or "Single Viral" in item["product"] or "Mega View" in item["product"] or "Trending Solo" in item["product"] or "Viral Reel" in item["product"]:
        tag = " [SINGLE]"
    print(f"    #{i:2d} {item['product']:<25} Score:{item['momentum_score']:<8} V:{item['videos']:2d} C:{item['creators']:2d}{tag}")

print("\n  ** DISCOVERY:")
for i, item in enumerate(discovery_rank[:20], 1):
    tag = ""
    if "Spike" in item["product"] or "TikTok" in item["product"] or "Unknown" in item["product"] or "Sudden" in item["product"] or "Mystery" in item["product"] or "Flash" in item["product"]:
        tag = " [SPIKE]"
    elif "One Hit" in item["product"] or "Single Viral" in item["product"] or "Mega View" in item["product"] or "Trending Solo" in item["product"] or "Viral Reel" in item["product"]:
        tag = " [SINGLE]"
    elif "Premium" in item["product"] or "Viral Beauty" in item["product"] or "Korean" in item["product"] or "Elegant" in item["product"] or "Daily Outfit" in item["product"]:
        tag = " [WINNER]"
    print(f"    #{i:2d} {item['product']:<25} Score:{item['discovery_score']:<8} Conf:{item['confidence']}{tag}")

print()


# ================================================================
# VALIDATION REPORT
# ================================================================

def get_rank(ranking_list, product_name):
    for i, item in enumerate(ranking_list, 1):
        if item["product"] == product_name:
            return i
    return "-"

def avg_score_for_category(hasil_list, keywords):
    items = [h for h in hasil_list if any(k in h["product"] for k in keywords)]
    if not items:
        return 0
    return sum(it["momentum_score"] for it in items) / len(items)

print("=" * 60)
print("  VALIDATION REPORT")
print("=" * 60)

print("""
  1. TRUE WINNER PRODUCTS (should be in Momentum TOP)
""")
for name in ["Premium Dress", "Viral Beauty Serum", "Korean Bag", "Elegant Shoes", "Daily Outfit"]:
    mr = get_rank(momentum_rank, name)
    dr = get_rank(discovery_rank, name)
    print(f"     {name:<25}  Momentum:#{mr:<3} Discovery:#{dr}")

print("""
  2. VIRAL SPIKE PRODUCTS (should NOT be Momentum #1, should be in Discovery)
""")
for name in ["New TikTok Find", "Unknown Product", "Sudden Viral", "Mystery Item", "Flash Trend"]:
    mr = get_rank(momentum_rank, name)
    dr = get_rank(discovery_rank, name)
    print(f"     {name:<25}  Momentum:#{mr:<3} Discovery:#{dr}")

print("""
  3. OLD VIRAL PRODUCTS (should have dropped in Momentum)
""")
for name in ["Old Fashion Trend", "Former Viral Dress", "Last Year Hit", "Classic Jacket", "Timeless Heels"]:
    mr = get_rank(momentum_rank, name)
    dr = get_rank(discovery_rank, name)
    print(f"     {name:<25}  Momentum:#{mr:<3} Discovery:#{dr}")

print("""
  4. FAKE TREND / NOISE (should be at bottom of Momentum)
""")
for i in range(1, 11):
    name = f"Fake Trend {i}"
    mr = get_rank(momentum_rank, name)
    dr = get_rank(discovery_rank, name)
    print(f"     {name:<25}  Momentum:#{mr:<3} Discovery:#{dr}")

print("""
  5. SINGLE VIDEO VIRAL (Discovery high, Momentum low)
""")
for name in ["One Hit Wonder", "Single Viral Clip", "Mega View Item", "Trending Solo", "Viral Reel"]:
    mr = get_rank(momentum_rank, name)
    dr = get_rank(discovery_rank, name)
    print(f"     {name:<25}  Momentum:#{mr:<3} Discovery:#{dr}")

print("""
  6. STABLE SLOW WINNERS (should rank reasonably in Momentum)
""")
for name in ["Basic Tee", "Comfort Pants", "Everyday Skincare", "Home Decor Set", "Kitchen Tool"]:
    mr = get_rank(momentum_rank, name)
    dr = get_rank(discovery_rank, name)
    print(f"     {name:<25}  Momentum:#{mr:<3} Discovery:#{dr}")

print()

# --- Summary Stats ---
mom_winner_avg = avg_score_for_category(momentum_rank, ["Premium", "Viral Beauty", "Korean Bag", "Elegant Shoes", "Daily Outfit"])
mom_spike_avg = avg_score_for_category(momentum_rank, ["New TikTok", "Unknown", "Sudden", "Mystery", "Flash"])
mom_old_avg = avg_score_for_category(momentum_rank, ["Old Fashion", "Former", "Last Year", "Classic", "Timeless"])
mom_noise_avg = avg_score_for_category(momentum_rank, ["Fake Trend"])
mom_single_avg = avg_score_for_category(momentum_rank, ["One Hit", "Single Viral", "Mega View", "Trending Solo", "Viral Reel"])

print("=" * 60)
print("  SUMMARY: AVERAGE MOMENTUM SCORE BY CATEGORY")
print("=" * 60)
print(f"  True Winner         : {mom_winner_avg:.2f}  (should be highest)")
print(f"  Stable Slow Winner  : {avg_score_for_category(momentum_rank, ['Basic Tee', 'Comfort Pants', 'Everyday Skincare', 'Home Decor', 'Kitchen Tool']):.2f}")
print(f"  Old Viral           : {mom_old_avg:.2f}  (should be lower than winners)")
print(f"  Viral Spike         : {mom_spike_avg:.2f}  (should be penalized)")
print(f"  Single Video Viral   : {mom_single_avg:.2f}  (should be heavily penalized)")
print(f"  Fake Trend / Noise  : {mom_noise_avg:.2f}  (should be lowest)")
print("=" * 60)
print()