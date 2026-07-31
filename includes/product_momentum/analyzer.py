"""
Product Momentum Analyzer.

Mengimplementasikan algoritma momentum dan discovery product
yang telah divalidasi (sebelumnya di hitung.py).
"""

import math
import statistics
import logging
from datetime import datetime

from includes.mysql import (
    get_product_momentum_data,
    get_product_avg_view_stats,
)
from includes.product_momentum.models import (
    ProductSummary,
    ChartData,
    empty_chart_data,
)

logger = logging.getLogger(__name__)


# ================================================================
# TAHAP 1: HITUNG DAILY GROWTH
# ================================================================

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
# Klasifikasi Status Produk
# ================================================================

def classify_product(item):
    """
    Mengklasifikasikan status produk berdasarkan analisis.

    Returns:
        str: Salah satu dari 'Winner', 'Stable', 'Spike', 'Old',
             'Noise', 'Single'
    """
    product_name = item["product"]
    momentum = item["momentum_score"]
    discovery = item["discovery_score"]
    videos = item["videos"]
    creators = item["creators"]
    consistency = item.get("consistency", 0)
    stability = item.get("stability", 0)
    penalty = item.get("penalty", 1.0)

        # Single video penalty
    if penalty <= 0.5 and videos <= 2:
        return "Single"

    # High momentum + high consistency + banyak video/creator = Winner
    if momentum >= 150 and videos >= 5 and creators >= 3 and consistency >= 0.6:
        return "Winner"

    # Momentum sedang + stability tinggi = Stable
    if momentum >= 80 and stability >= 0.7 and videos >= 3:
        return "Stable"

    # Discovery tinggi tapi momentum rendah = Spike
    if discovery > momentum * 1.5 and videos <= 3:
        return "Spike"

    # Momentum rendah + banyak video = Old (pernah populer, sekarang turun)
    if momentum < 60 and videos >= 5 and consistency < 0.4:
        return "Old"

    # Consistency sangat rendah = Noise
    if consistency < 0.35 and momentum < 80:
        return "Noise"

    # Default untuk yang tidak masuk kategori lain
    if momentum >= 100:
        return "Winner"
    elif momentum >= 60:
        return "Stable"
    elif discovery > momentum:
        return "Spike"
    elif consistency < 0.4:
        return "Noise"
    else:
        return "Stable"


def get_status_badge_color(status):
    """Mengembalikan warna badge Tabler untuk setiap status."""
    colors = {
        "Winner": "bg-green-lt text-green",
        "Stable": "bg-blue-lt text-blue",
        "Spike":  "bg-orange-lt text-orange",
        "Old":    "bg-yellow-lt text-yellow",
        "Noise":  "bg-red-lt text-red",
        "Single": "bg-purple-lt text-purple",
    }
    return colors.get(status, "bg-secondary-lt text-secondary")


# ================================================================
# ProductMomentumAnalyzer
# ================================================================

class ProductMomentumAnalyzer:
    """
    Menganalisis momentum produk berdasarkan data video TikTok
    yang diambil dari database.
    """

    def __init__(self):
        self.raw_data = []
        self.produk_data = {}
        self.hasil = []
        self.summary = None
        self.chart_data = None
        self.avg_view_stats = []

    # ---------------------------------------------------------------
    # COLLECT DATA
    # ---------------------------------------------------------------

    def collect_data(self):
        """
        Mengambil data dari database via mysql.py.
        Data berupa list video dengan daily views per produk.

        Returns:
            list[dict]: Data mentah dari database
        """
        logger.info("Mengambil data product momentum dari database...")
        self.raw_data = get_product_momentum_data()
        logger.info(f"Data terkumpul: {len(self.raw_data)} record video")
        return self.raw_data

    def collect_avg_view_stats(self):
        """
        Mengambil statistik rata-rata view per produk langsung dari
        database (GROUP BY + aggregate). Creator tidak menjadi pembeda;
        hanya produk yang menjadi pengelompokan. Setiap video hanya
        dihitung sekali menggunakan snapshot view terbarunya.

        Returns:
            list[dict]: Data avg view per produk, urut Average View DESC
        """
        self.avg_view_stats = get_product_avg_view_stats()
        return self.avg_view_stats

    # ---------------------------------------------------------------
    # PROSES DATA MENTAH -> PRODUK_DATA
    # ---------------------------------------------------------------

    def process_raw_data(self):
        """
        Mengelompokkan data mentah per produk,
        menghitung growth, weighted growth, dan konsistensi per video.
        """
        self.produk_data = {}

        for item in self.raw_data:
            product_name = item["product_name"]
            video_id = item["video_id"]
            creator = item["creator_name"]
            daily_views = item["daily_views"]

            if not daily_views or len(daily_views) < 2:
                continue

            # Hitung daily growth
            growths = hitung_daily_growth(daily_views)

            # Hitung weighted growth (dengan recency weight)
            weighted_growth = hitung_weighted_growth(growths)

            # Hitung konsistensi
            konsistensi = hitung_konsistensi(growths)

            # Average views & median views
            avg_view = sum(daily_views) / len(daily_views) if daily_views else 0
            sorted_views = sorted(daily_views)
            n = len(sorted_views)
            if n % 2 == 0:
                median_view = (sorted_views[n//2 - 1] + sorted_views[n//2]) / 2
            else:
                median_view = sorted_views[n//2]

            # Trend: growth positif dalam 3 hari terakhir
            recent_3_days = daily_views[-3:] if len(daily_views) >= 3 else daily_views
            trend = "up" if len(recent_3_days) >= 2 and recent_3_days[-1] > recent_3_days[0] else "stable"
            if len(recent_3_days) >= 2 and recent_3_days[-1] < recent_3_days[0]:
                trend = "down"

            video_info = {
                "video_id": video_id,
                "creator": creator,
                "weighted_growth": weighted_growth,
                "konsistensi": konsistensi,
                "avg_view": avg_view,
                "median_view": median_view,
                "trend": trend,
                "last_update": item.get("last_scan", datetime.now()),
            }

            if product_name not in self.produk_data:
                self.produk_data[product_name] = {
                    "videos": [],
                    "creators": set(),
                                        "product_id": item.get("product_id"),
                    "tiktok_id_product": item.get("tiktok_id_product"),
                }

            self.produk_data[product_name]["videos"].append(video_info)
            self.produk_data[product_name]["creators"].add(creator)

        return self.produk_data

    # ---------------------------------------------------------------
    # HITUNG METRIK PER PRODUK
    # ---------------------------------------------------------------

    def calculate_metrics(self):
        """
        Menghitung seluruh metrik per produk:
        - Average Video Growth
        - Confidence (Video Validation)
        - Creator Factor (Logarithmic)
        - Consistency
        - Stability (Growth Distribution)
        - Single Viral Penalty
        - Growth Score dengan Exposure Factor
        - Momentum Score
        - Discovery Score
        """
        self.hasil = []

        for product_name, pdata in self.produk_data.items():
            videos = pdata["videos"]
            creators = pdata["creators"]

            video_count = len(videos)
            creator_count = len(creators)

            # --- A. Average Video Growth ---
            total_weighted_growth = sum(v["weighted_growth"] for v in videos)
            avg_weighted_growth = total_weighted_growth / video_count if video_count > 0 else 0

                        # --- B. Video Validation (Confidence) ---
            # Confidence = kombinasi video_count + creator_count + spread
            # Tujuannya: 5 video dari 5 creator != 5 video dari 1 creator
            video_confidence = min(video_count / 5.0, 1.0)
            creator_confidence = min(creator_count / 3.0, 1.0)
            if video_count > 0:
                creator_ratio = creator_count / video_count
                spread_factor = min(creator_ratio * 2.0, 1.0)
            else:
                spread_factor = 0.0
            confidence = video_confidence * 0.5 + creator_confidence * 0.3 + spread_factor * 0.2

            # --- C. Creator Factor (Logarithmic) ---
            if creator_count > 0:
                creator_factor = min(
                    math.log(creator_count + 1) / math.log(6),
                    1.0
                )
            else:
                creator_factor = 0.0

            # --- D. Consistency ---
            avg_konsistensi = sum(v["konsistensi"] for v in videos) / video_count if video_count > 0 else 0

                        # --- E. Stability (Growth Distribution) ---
            # Gunakan Coefficient of Variation (CV) supaya scale-invariant
            # Produk kecil maupun besar dinilai secara adil
            growth_values = [v["weighted_growth"] for v in videos]

            if video_count > 1:
                growth_std = statistics.stdev(growth_values)
            else:
                growth_std = 0

            # Hitung mean absolute growth untuk CV
            mean_abs_growth = sum(abs(g) for g in growth_values) / len(growth_values) if growth_values else 0
            if mean_abs_growth > 0:
                cv = growth_std / mean_abs_growth  # Coefficient of Variation
            else:
                cv = 0
            stability = 1.0 / (1.0 + cv)

                        # --- F. Single Viral Penalty ---
            # Penalty smooth: berdasarkan video_count DAN creator_count
            # 1 vid/1 cr = 0.40, 2 vid/1 cr = 0.60, 2 vid/2 cr = 0.80, 3+ vid = 1.0
            base_penalty = min(video_count / 3.0, 1.0)
            creator_boost = min(creator_count / 2.0, 1.0)
            penalty = base_penalty * 0.6 + creator_boost * 0.4
            penalty = max(penalty, 0.4)

            # --- G. Growth Score dengan Exposure Factor ---
            exposure_factor = math.log(video_count + 1)
            safe_growth = max(avg_weighted_growth, 0)
            growth_score = math.sqrt(safe_growth) * exposure_factor

                        # --- H. Momentum Score ---
            momentum_score = (
                growth_score * 0.45
                + confidence * 100 * 0.20
                + creator_factor * 100 * 0.15
                + avg_konsistensi * 100 * 0.10
                + stability * 100 * 0.10
            )
            # Simpan raw_score sebelum penalty
            raw_score = momentum_score
            # Terapkan penalty untuk produk dengan sedikit video/creator
            momentum_score = momentum_score * penalty

            # Breakdown untuk explainability (debugging)
            score_breakdown = {
                "growth_pct": round(growth_score * 0.45, 2),
                "confidence_pct": round(confidence * 100 * 0.20, 2),
                "creator_pct": round(creator_factor * 100 * 0.15, 2),
                "consistency_pct": round(avg_konsistensi * 100 * 0.10, 2),
                "stability_pct": round(stability * 100 * 0.10, 2),
                "raw_score": round(raw_score, 2),
                "penalty": round(penalty, 2),
                "final_score": round(momentum_score, 2),
            }

                        # --- I. Discovery Score ---
            # Discovery = growth_potential * (1 - confidence*0.7) * consistency * creator_diversity
            # (1 - confidence*0.7) agar produk established tetap bisa punya discovery non-zero
            # Creator diversity: lebih dari 1 creator = lebih terpercaya
            if video_count > 0:
                creator_ratio = creator_count / video_count
                creator_diversity = min(creator_ratio * 3.0, 1.0)
            else:
                creator_diversity = 0.0
            discovery_score = (
                growth_score
                * (1 - confidence * 0.7)  # Max discount 70%, bukan 100%
                * (0.5 + avg_konsistensi)
                * (0.5 + creator_diversity * 0.5)  # Range: 0.5 (1 creator) - 1.0 (banyak creator)
            )

            # --- Statistik View tambahan ---
            all_views = []
            all_trends = set()
            last_updates = []
            for v in videos:
                if "daily_views_raw" in v:
                    all_views.extend(v["daily_views_raw"])
                all_trends.add(v.get("trend", "stable"))
                if v.get("last_update"):
                    last_updates.append(v["last_update"])

            avg_view_all = sum(all_views) / len(all_views) if all_views else 0
            sorted_views_all = sorted(all_views)
            n_all = len(sorted_views_all)
            if n_all % 2 == 0 and n_all > 0:
                median_view_all = (sorted_views_all[n_all//2 - 1] + sorted_views_all[n_all//2]) / 2
            elif n_all > 0:
                median_view_all = sorted_views_all[n_all//2]
            else:
                median_view_all = 0

            # Trend dominan
            if "up" in all_trends and len(all_trends) == 1:
                trend_overall = "up"
            elif "down" in all_trends and len(all_trends) == 1:
                trend_overall = "down"
            else:
                trend_overall = "stable"

            last_update = max(last_updates) if last_updates else datetime.now()
            if isinstance(last_update, datetime):
                last_update_str = last_update.strftime("%Y-%m-%d %H:%M")
            else:
                last_update_str = str(last_update)[:16]

            self.hasil.append({
                "product": product_name,
                "product_id": pdata.get("product_id"),
                "tiktok_id_product": pdata.get("tiktok_id_product"),
                "momentum_score": round(momentum_score, 2),
                "discovery_score": round(discovery_score, 2),
                "score_breakdown": score_breakdown,
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
                "avg_view": round(avg_view_all),
                "median_view": round(median_view_all),
                "trend": trend_overall,
                "last_update": last_update_str,
            })

        return self.hasil

    # ---------------------------------------------------------------
    # KLASIFIKASI
    # ---------------------------------------------------------------

    def classify_results(self):
        """Menambahkan status/klasifikasi pada setiap hasil."""
        for item in self.hasil:
            item["status"] = classify_product(item)
            item["status_color"] = get_status_badge_color(item["status"])
        return self.hasil

    # ---------------------------------------------------------------
    # BUILD SUMMARY
    # ---------------------------------------------------------------

    def build_summary(self):
        """Membangun ringkasan statistik."""
        if not self.hasil:
            self.summary = ProductSummary(
                total_products=0,
                products_analyzed=0,
                total_creators=0,
                total_videos=0,
                avg_momentum=0,
                highest_momentum=0,
                highest_momentum_product="",
            )
            return self.summary

        total_products = len(self.hasil)
        total_videos = sum(h["videos"] for h in self.hasil)
        total_creators_all = set()
        for pname, pdata in self.produk_data.items():
            total_creators_all.update(pdata["creators"])

        momentum_values = [h["momentum_score"] for h in self.hasil]
        avg_momentum = sum(momentum_values) / len(momentum_values) if momentum_values else 0
        highest_idx = momentum_values.index(max(momentum_values)) if momentum_values else 0

        self.summary = ProductSummary(
            total_products=total_products,
            products_analyzed=len([h for h in self.hasil if h["videos"] > 0]),
            total_creators=len(total_creators_all),
            total_videos=total_videos,
            avg_momentum=round(avg_momentum, 2),
            highest_momentum=round(max(momentum_values), 2) if momentum_values else 0,
            highest_momentum_product=self.hasil[highest_idx]["product"] if self.hasil else "",
        )
        return self.summary

    # ---------------------------------------------------------------
    # BUILD CHART DATA
    # ---------------------------------------------------------------

    def build_chart_data(self):
        """Menyiapkan data untuk grafik."""
        if not self.hasil:
            self.chart_data = empty_chart_data()
            return self.chart_data

        # Urutkan berdasarkan momentum
        momentum_ranked = sorted(self.hasil, key=lambda x: x["momentum_score"], reverse=True)
        discovery_ranked = sorted(self.hasil, key=lambda x: x["discovery_score"], reverse=True)

        # --- Top 10 Momentum (Horizontal Bar) ---
        top_momentum = momentum_ranked[:10]
        chart_momentum = {
            "labels": [h["product"] for h in reversed(top_momentum)],
            "data": [h["momentum_score"] for h in reversed(top_momentum)],
            "colors": ["#206bc4"] * len(top_momentum),
        }

        # --- Top 10 Discovery (Horizontal Bar) ---
        top_discovery = discovery_ranked[:10]
        chart_discovery = {
            "labels": [h["product"] for h in reversed(top_discovery)],
            "data": [h["discovery_score"] for h in reversed(top_discovery)],
            "colors": ["#2fb344"] * len(top_discovery),
        }

        # --- Distribusi Momentum ---
        ranges = [
            ("0 - 50", 0, 50),
            ("50 - 100", 50, 100),
            ("100 - 150", 100, 150),
            ("150+", 150, float("inf")),
        ]
        distribution = []
        for label, low, high in ranges:
            count = sum(1 for h in self.hasil if low <= h["momentum_score"] < high)
            distribution.append({"label": label, "count": count})

        chart_distribution = {
            "labels": [d["label"] for d in distribution],
            "data": [d["count"] for d in distribution],
            "colors": ["#d63939", "#f59f00", "#17a2b8", "#2fb344"],
        }

        # --- Distribusi Kategori (jika ada data kategori) ---
        # Klasifikasi berdasarkan status
        status_counts = {}
        for h in self.hasil:
            s = h.get("status", "Unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        chart_category = {
            "labels": list(status_counts.keys()),
            "data": list(status_counts.values()),
            "colors": {
                "Winner": "#2fb344",
                "Stable": "#206bc4",
                "Spike": "#f59f00",
                "Old": "#ff922b",
                "Noise": "#d63939",
                "Single": "#ae3ec9",
            },
        }

        self.chart_data = ChartData(
            momentum=chart_momentum,
            discovery=chart_discovery,
            distribution=chart_distribution,
            category=chart_category,
        )
        return self.chart_data

    # ---------------------------------------------------------------
    # FULL ANALYSIS PIPELINE
    # ---------------------------------------------------------------

    def run(self, from_db=True):
        """
        Menjalankan seluruh pipeline analisis.

        Args:
            from_db: Jika True, ambil data dari database.
                     Jika False, data sudah di-set manual (untuk testing).

        Returns:
            dict: Dictionary berisi seluruh hasil analisis.
        """
        # 1. Collect Data
        if from_db:
            self.collect_data()

        # 2. Process Raw Data
        self.process_raw_data()

        # 3. Calculate Metrics
        self.calculate_metrics()

        # 4. Classify Results
        self.classify_results()

        # 5. Build Summary
        self.build_summary()

        # 6. Build Chart Data
        self.build_chart_data()

        # 7. Collect Avg View Per Product (tabel baru)
        self.collect_avg_view_stats()

        return self.get_results()

    # ---------------------------------------------------------------
    # GET RESULTS
    # ---------------------------------------------------------------

    def get_results(self):
        """Mengembalikan seluruh hasil analisis dalam bentuk dictionary."""
        # Momentum ranking
        momentum_ranked = sorted(
            self.hasil, key=lambda x: x["momentum_score"], reverse=True
        )
        # Discovery ranking
        discovery_ranked = sorted(
            self.hasil, key=lambda x: x["discovery_score"], reverse=True
        )

        return {
            "summary": self.summary._asdict() if self.summary else {},
            "momentum_rank": momentum_ranked,
            "discovery_rank": discovery_ranked,
            "all_results": self.hasil,
            "chart_data": self.chart_data._asdict() if self.chart_data else {},
            "total_products": len(self.hasil),
            "avg_view_per_product": self.avg_view_stats,
        }


# ================================================================
# CONVENIENCE FUNCTION
# ================================================================

def analyze_product_momentum():
    """
    Fungsi convenience untuk menjalankan analisis product momentum
    dengan data dari database.

    Returns:
        dict: Hasil analisis lengkap
    """
    analyzer = ProductMomentumAnalyzer()
    return analyzer.run(from_db=True)
