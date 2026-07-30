# Product Momentum Algorithm ? Dokumentasi

## Ringkasan

Algoritma Product Momentum menganalisis produk TikTok berdasarkan data
video harian. Tujuan utamanya adalah mengidentifikasi produk yang sedang
"momentum" (tumbuh cepat dan konsisten) dan produk yang berpotensi
"discovery" (belum populer tetapi menunjukkan tanda pertumbuhan).

## Arsitektur

Data MySQL -> get_product_momentum_data() -> process_raw_data() -> calculate_metrics() -> classify_results() -> Output

---

## 1. DAILY GROWTH

### Rumus

growth[i] = daily_views[i] - daily_views[i-1]

Growth harian adalah selisih views antara hari ke-i dan hari ke-(i-1).

---

## 2. RECENCY WEIGHT

### Rumus

Untuk data 10 hari -> 9 growth periods:
weights[-3] = 0.2   # 3 hari terakhir
weights[-2] = 0.3   # 2 hari terakhir
weights[-1] = 0.5   # hari terakhir

Untuk data lebih pendek:
- 2 growth periods: [0.4, 0.6]
- 1 growth period:  [1.0]

---

## 3. CONFIDENCE (REVISED)

### Rumus Lama

confidence = min(video_count / 5.0, 1.0)

### Rumus Baru

video_confidence   = min(video_count / 5.0, 1.0)
creator_confidence = min(creator_count / 3.0, 1.0)
creator_ratio      = creator_count / video_count
spread_factor      = min(creator_ratio * 2.0, 1.0)
confidence = video_confidence * 0.5 + creator_confidence * 0.3 + spread_factor * 0.2

### Bobot

| Komponen          | Bobot | Alasan                                    |
|-------------------|-------|-------------------------------------------|
| Video Confidence  | 0.50  | Jumlah video masih indikator terpenting    |
| Creator Confidence| 0.30  | Creator diversity menambah kepercayaan     |
| Spread Factor     | 0.20  | Distribusi video antar creator             |

### Contoh

5 video/5 creator: 1.00*0.5 + 1.00*0.3 + 1.00*0.2 = 1.00
5 video/1 creator: 1.00*0.5 + 0.33*0.3 + 0.40*0.2 = 0.68
3 video/3 creator: 0.60*0.5 + 1.00*0.3 + 1.00*0.2 = 0.80
1 video/1 creator: 0.20*0.5 + 0.33*0.3 + 1.00*0.2 = 0.40

---

## 4. CREATOR FACTOR (Tidak Diubah)

creator_factor = min(log(creator_count + 1) / log(6), 1.0)

---

## 5. CONSISTENCY (Tidak Diubah)

consistency = count(growth > 0) / total_growth_periods

---

## 6. STABILITY (REVISED)

### Rumus Lama

stability = 1.0 / (1.0 + growth_std / 100000.0)

### Rumus Baru - Coefficient of Variation (CV)

mean_abs_growth = mean(|g| for g in growth_values)
cv = growth_std / mean_abs_growth
stability = 1.0 / (1.0 + cv)

### Alasan

CV adalah ukuran dispersi scale-invariant. Produk dengan views kecil maupun
besar dinilai secara adil.

---

## 7. PENALTY (REVISED)

### Rumus Lama

if video_count == 1:     penalty = 0.25
elif video_count == 2:   penalty = 0.50
else:                    penalty = 1.0

### Rumus Baru

base_penalty  = min(video_count / 3.0, 1.0)
creator_boost = min(creator_count / 2.0, 1.0)
penalty       = base_penalty * 0.6 + creator_boost * 0.4
penalty       = max(penalty, 0.4)

---

## 8. GROWTH SCORE (Tidak Diubah)

exposure_factor = log(video_count + 1)
safe_growth     = max(avg_weighted_growth, 0)
growth_score    = sqrt(safe_growth) * exposure_factor

### Evaluasi sqrt()

sqrt adalah pilihan paling sesuai karena:
- Memberi diminishing returns yang wajar
- Tidak terlalu agresif (seperti linear)
- Tidak terlalu flat (seperti log)

---

## 9. MOMENTUM SCORE (Bobot Tidak Diubah)

momentum = growth_score*0.45 + confidence*100*0.20 + creator_factor*100*0.15
        + consistency*100*0.10 + stability*100*0.10
momentum = momentum * penalty

### Evaluasi Bobot

Growth (45%) sebagai komponen terbesar memang tepat.
Confidence (20%), Creator (15%), Consistency (10%), Stability (10%) seimbang.
Tidak perlu diubah.

---

## 10. DISCOVERY SCORE (REVISED)

### Rumus Lama

discovery = growth_score * (1 - confidence) * (0.5 + consistency)

### Rumus Baru

creator_ratio     = creator_count / video_count
creator_diversity = min(creator_ratio * 3.0, 1.0)

discovery = growth_score
          * (1 - confidence * 0.7)
          * (0.5 + consistency)
          * (0.5 + creator_diversity * 0.5)

### Perubahan

| Aspek              | Lama                | Baru                  |
|--------------------|---------------------|-----------------------|
| Discount conf      | (1-conf) max 100%   | (1-conf*0.7) max 70%  |
| Creator diversity  | Tidak ada           | (0.5+div*0.5)         |
| Disc untuk established| 0                | Non-zero              |

---

## 11. EXPLAIN SCORE (BARU)

Setiap produk memiliki score_breakdown untuk debugging:
- growth_pct, confidence_pct, creator_pct
- consistency_pct, stability_pct
- raw_score, penalty, final_score

---

## 12. KLASIFIKASI STATUS

| Status   | Threshold                                        |
|----------|--------------------------------------------------|
| Single   | penalty <= 0.5 AND videos <= 2                   |
| Winner   | momentum >= 150 AND vid >= 5 AND cr >= 3 AND kon >= 0.6 |
| Stable   | momentum >= 80 AND stability >= 0.7 AND vid >= 3 |
| Spike    | discovery > momentum*1.5 AND videos <= 3         |
| Old      | momentum < 60 AND vid >= 5 AND kon < 0.4        |
| Noise    | konsistensi < 0.35 AND momentum < 80             |

---

## 13. POTENSI BIAS YANG DIKURANGI

| Bias Sebelumnya                          | Status      |
|------------------------------------------|-------------|
| 5 vid/1 cr = 5 vid/5 cr (confidence)    | Diperbaiki  |
| Stability ~0.999 semua produk            | Diperbaiki  |
| Discovery = 0 untuk produk established   | Diperbaiki  |
| Single video dominasi discovery          | Diperbaiki  |
| Penalty 0.25/0.50/1.0 terlalu agresif    | Diperbaiki  |
| Tidak ada breakdown debugging            | Ditambahkan |
