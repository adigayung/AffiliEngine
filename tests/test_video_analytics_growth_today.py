"""
Regression test untuk sinkronisasi "Perubahan Hari Ini" (summary Growth)
dengan daily views chart pada halaman /creator/<id>/video_analytics.

Konteks bug (creator_id = 2 / "Kang Petruk"):
    Summary "Perubahan Hari Ini" = +27.177
    Chart hari ini               = +9.053
    27.177 = 9.053 (snapshot hari ini) + 18.124 (snapshot STALE)

Summary lama memakai 2 snapshot terakhir per video TANPA filter tanggal,
sehingga video yang snapshot terakhirnya BUKAN hari ini tetap dihitung.
Perbaikan: summary hanya menjumlahkan growth dari snapshot yang bertanggal
HARI INI (`views_growth_today`), dengan kontrak delta `max(0, delta)` supaya
konsisten dengan chart (get_creator_daily_views_chart).

File ini memakai fake connection (tanpa MySQL asli) dan meniru semantik SQL
yang dipakai service (ROW_NUMBER 2-terakhir untuk summary; latest-per-(video,
tanggal) + baseline untuk chart).

Jalankan:
    python -m unittest tests.test_video_analytics_growth_today -v
"""

import sys
import types
import unittest
from datetime import datetime, timedelta, time
from unittest import mock

# ------------------------------------------------------------------
# STUB dependensi berat (seleniumbase/PIL) yang tak dibutuhkan untuk
# mengimpor service layer. Harus dipasang SEBELUM import service.
# ------------------------------------------------------------------
if "includes.tiktok_scrape_videos" not in sys.modules:
    _fake_scraper_mod = types.ModuleType("includes.tiktok_scrape_videos")

    class _FakeTikTokScraper:  # placeholder; tidak dipakai di test ini
        def __init__(self, *args, **kwargs):
            pass

    _fake_scraper_mod.TikTokScraper = _FakeTikTokScraper
    # Service layer mengimpor MAX_VIDEOS dari paket ini; stub harus
    # menyediakannya agar import tidak gagal (nilai mengikuti scraper asli).
    _fake_scraper_mod.MAX_VIDEOS = 190
    _fake_scraper_mod.MAX_SCROLLS = 8
    sys.modules["includes.tiktok_scrape_videos"] = _fake_scraper_mod

import includes.video_analytics.video_analytics as va  # noqa: E402
import routers.creator.video_analytics as rva  # noqa: E402


# ==================================================================
# Emulasi semantik SQL service (dipakai oleh FakeCursor di bawah)
# ==================================================================
def _snap_date(snapshot_time):
    return snapshot_time.date() if isinstance(snapshot_time, datetime) else snapshot_time


def _two_latest(snapshots, video_ids):
    """Tiru query summary: 2 snapshot terakhir per video (ROW_NUMBER rn<=2)."""
    rows = []
    for vid in video_ids:
        snaps = sorted(
            [s for s in snapshots if s["video_id"] == int(vid)],
            key=lambda x: x["snapshot_time"],
            reverse=True,
        )[:2]
        for s in snaps:
            rows.append({
                "video_id": str(vid),  # mirror VARCHAR di DB
                "views": s["views"],
                "likes": s.get("likes", 0),
                "comments": s.get("comments", 0),
                "shares": s.get("shares", 0),
                "favorites": s.get("favorites", 0),
                "snapshot_time": s["snapshot_time"],
                "created_at": s["snapshot_time"],
            })
    return rows


def _latest_per_day(snapshots, lo, hi, creator_id):
    """Tiru chart STEP 1: latest snapshot per (video_id, DATE) dalam [lo, hi)."""
    best = {}
    for s in snapshots:
        d = _snap_date(s["snapshot_time"])
        if d is None or d < lo or d >= hi:
            continue
        key = (s["video_id"], d)
        if key not in best or s["snapshot_time"] > best[key][0]:
            best[key] = (s["snapshot_time"], s["views"])
    return [
        {"creator_id": creator_id, "tgl": d, "video_id": vid, "views": views}
        for (vid, d), (_ts, views) in best.items()
    ]


def _baseline_before(snapshots, before):
    """Tiru chart STEP 0: latest snapshot per video sebelum `before`."""
    best = {}
    for s in snapshots:
        d = _snap_date(s["snapshot_time"])
        if d is None or d >= before:
            continue
        if s["video_id"] not in best or s["snapshot_time"] > best[s["video_id"]][0]:
            best[s["video_id"]] = (s["snapshot_time"], s["views"])
    return [{"video_id": vid, "views": v} for vid, (_ts, v) in best.items()]


# ==================================================================
# FAKE DATABASE
# ==================================================================
class FakeCursor:
    def __init__(self, store):
        self.store = store
        self._rows = []
        self._single = None

    def execute(self, sql, params=None):
        norm = " ".join(sql.split())
        self.store["calls"].append((norm, params))

        if norm.startswith("SELECT v.id,"):
            # Daftar video (summary)
            self._rows = [dict(r) for r in self.store["video_rows"]]
        elif "ROW_NUMBER() OVER" in norm:
            # 2 snapshot terakhir per video (summary)
            self._rows = _two_latest(self.store["snapshots"], list(params or []))
        elif norm.startswith("SELECT MAX(last_scan)"):
            self._single = {"last_scan": self.store.get("last_scan")}
        elif norm.startswith("SELECT v.creator_id,"):
            # chart STEP 1
            start_date, end_plus, creator_id = params
            self._rows = _latest_per_day(
                self.store["snapshots"], start_date, end_plus, creator_id
            )
        elif norm.startswith("SELECT s.video_id, s.views"):
            # chart STEP 0 (baseline)
            start_date, creator_id = params
            self._rows = _baseline_before(self.store["snapshots"], start_date)
        else:
            raise AssertionError("Unexpected SQL: " + norm)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._single

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConnection:
    def __init__(self, store):
        self.store = store

    def cursor(self):
        return FakeCursor(self.store)

    def close(self):
        pass


# ==================================================================
# TEST CASE
# ==================================================================
class GrowthTodayTestCase(unittest.TestCase):
    def setUp(self):
        self.today = datetime.now().date()
        self.store = {"video_rows": [], "snapshots": [], "calls": [], "last_scan": None}

    # ---------------- helpers ----------------
    def _add_video(self, pk, tiktok_id):
        self.store["video_rows"].append({
            "id": pk,
            "video_id": tiktok_id,
            "video_url": f"https://www.tiktok.com/@x/video/{tiktok_id}",
            "caption": f"video {pk}",
            "upload_time": datetime(2026, 9, 1, 12, 0, 0),
            "last_scan": datetime.now(),
            "duration": 30,
            "match_score": None,
            "match_method": None,
            "matched_at": None,
            "upload_job_id": None,
            "upload_product_id": None,
            "product_title": None,
            "product_tiktok_id": None,
        })

    def _add_snapshot(self, pk, days_ago, views):
        self.store["snapshots"].append({
            "video_id": pk,
            "views": views,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "favorites": 0,
            "snapshot_time": datetime.combine(
                self.today - timedelta(days=days_ago), time(10, 0)
            ),
        })

    def _read(self):
        with mock.patch.object(va, "get_connection", lambda: FakeConnection(self.store)):
            return va.video_analytics_service._read_analytics(2)

    def _chart(self):
        with mock.patch.object(va, "get_connection", lambda: FakeConnection(self.store)):
            return va.video_analytics_service.get_creator_daily_views_chart(2)

    def _video(self, analytics, pk):
        return next(v for v in analytics["videos"] if v["id"] == pk)

    # ---------------- unit: helper tanggal ----------------
    def test_as_date_parsing(self):
        dt = datetime(2026, 9, 23, 10, 0, 0)
        self.assertEqual(va._as_date(dt), self.today.__class__(2026, 9, 23))
        self.assertEqual(va._as_date("2026-09-23 10:00:00"), self.today.__class__(2026, 9, 23))
        self.assertIsNone(va._as_date(None))
        self.assertIsNone(va._as_date("bukan-tanggal"))

    # ---------------- acceptance: current snapshot = today ----------------
    def test_curr_snapshot_today_contributes_delta(self):
        self._add_video(10, "111")
        self._add_snapshot(10, days_ago=1, views=1000)          # kemarin
        self._add_snapshot(10, days_ago=0, views=1500)          # hari ini

        analytics = self._read()
        v = self._video(analytics, 10)

        self.assertTrue(v["snapshot_is_today"])
        self.assertEqual(v["views_growth_today"], 500)
        self.assertEqual(v["views_growth"], 500)

    # ---------------- acceptance: current snapshot = stale ----------------
    def test_stale_snapshot_contributes_zero(self):
        # Video 1561 pada kasus Kang Petruk: snapshot terakhir 3 hari lalu.
        self._add_video(1561, "7682446872346201362")
        self._add_snapshot(1561, days_ago=4, views=51200)
        self._add_snapshot(1561, days_ago=3, views=69324)       # stale (bukan hari ini)

        analytics = self._read()
        v = self._video(analytics, 1561)

        self.assertFalse(v["snapshot_is_today"])
        self.assertEqual(v["views_growth_today"], 0)            # TIDAK masuk "hari ini"
        self.assertEqual(v["views_growth"], 18124)              # growth terakhir tetap ada

    # ---------------- acceptance: delta negatif -> max(0, delta) ----------------
    def test_negative_delta_clamped_to_zero(self):
        self._add_video(20, "222")
        self._add_snapshot(20, days_ago=1, views=2000)          # kemarin
        self._add_snapshot(20, days_ago=0, views=1800)          # hari ini turun

        analytics = self._read()
        v = self._video(analytics, 20)

        self.assertTrue(v["snapshot_is_today"])
        self.assertEqual(v["views_growth_today"], 0)            # clamp max(0, -200)

    # ---------------- acceptance: single snapshot hari ini ----------------
    def test_today_without_prev_zero(self):
        self._add_video(30, "333")
        self._add_snapshot(30, days_ago=0, views=777)           # snapshot pertama = hari ini

        v = self._video(self._read(), 30)
        self.assertTrue(v["snapshot_is_today"])
        self.assertEqual(v["views_growth_today"], 0)            # chart -> base None -> 0

    # ---------------- acceptance: invariant summary == chart (Kang Petruk) ----------------
    def test_invariant_summary_today_equals_chart_today(self):
        # 91 video dengan snapshot hari ini: 90 x 100 + 1 x 53 = 9.053
        deltas = [100] * 90 + [53]
        for i, delta in enumerate(deltas, start=1):
            self._add_video(i, f"today-{i}")
            base = 1000 + i
            self._add_snapshot(i, days_ago=1, views=base)
            self._add_snapshot(i, days_ago=0, views=base + delta)

        # 1 video stale (mirror video 1561): growth 18.124, TIDAK hari ini
        self._add_video(1561, "7682446872346201362")
        self._add_snapshot(1561, days_ago=4, views=51200)
        self._add_snapshot(1561, days_ago=3, views=51200 + 18124)

        analytics = self._read()
        summary_today = sum(v["views_growth_today"] for v in analytics["videos"])
        old_buggy_total = sum(v["views_growth"] for v in analytics["videos"])

        chart = self._chart()
        chart_series = chart["datasets"][0]["data"]
        chart_today = chart_series[-1]

        # Inti perbaikan
        self.assertEqual(summary_today, 9053)
        self.assertEqual(chart_today, 9053)
        self.assertEqual(summary_today, chart_today)

        # Angka lama (buggy) memang 27.177 — memastikan test benar-benar
        # mereproduksi kasus yang dilaporkan.
        self.assertEqual(old_buggy_total, 27177)

        # Video stale tidak menyumbang "hari ini".
        stale = self._video(analytics, 1561)
        self.assertEqual(stale["views_growth_today"], 0)

    # ---------------- acceptance #6: chart history tidak berubah ----------------
    def test_chart_books_stale_growth_on_its_own_date(self):
        self._add_video(1561, "7682446872346201362")
        self._add_snapshot(1561, days_ago=4, views=51200)
        self._add_snapshot(1561, days_ago=3, views=69300)

        self._add_video(10, "111")
        self._add_snapshot(10, days_ago=1, views=1000)
        self._add_snapshot(10, days_ago=0, views=1500)

        chart = self._chart()
        labels = chart["labels"]
        series = chart["datasets"][0]["data"]

        day3 = (self.today - timedelta(days=3)).strftime("%Y-%m-%d")
        today = self.today.strftime("%Y-%m-%d")

        # Growth stale dibukukan pada tanggal snapshot-nya (3 hari lalu),
        # bukan hari ini.
        self.assertEqual(series[labels.index(day3)], 18100)
        self.assertEqual(series[labels.index(today)], 500)

    # ---------------- router: summary memakai views_growth_today ----------------
    def test_router_summary_uses_today_growth(self):
        deltas = [100] * 90 + [53]
        for i, delta in enumerate(deltas, start=1):
            self._add_video(i, f"today-{i}")
            base = 1000 + i
            self._add_snapshot(i, days_ago=1, views=base)
            self._add_snapshot(i, days_ago=0, views=base + delta)

        self._add_video(1561, "7682446872346201362")
        self._add_snapshot(1561, days_ago=4, views=51200)
        self._add_snapshot(1561, days_ago=3, views=51200 + 18124)

        captured = {}

        def fake_render(name, **kwargs):
            captured["name"] = name
            captured["ctx"] = kwargs
            return "rendered"

        with mock.patch.object(va, "get_connection", lambda: FakeConnection(self.store)), \
                mock.patch.object(va.video_analytics_service, "get_rising_videos", lambda cid: []), \
                mock.patch.object(
                    va, "get_creator",
                    lambda cid: {"id": 2, "username": "kangpetruk", "display_name": "Kang Petruk"},
                ), \
                mock.patch.object(rva, "render_template", fake_render):
            rva.video_analytics(2)

        self.assertEqual(captured["name"], "video_analytics/index.html")
        ctx = captured["ctx"]

        summary_today = ctx["total_views_growth"]
        chart_today = ctx["daily_views_chart"]["datasets"][0]["data"][-1]

        self.assertEqual(summary_today, 9053)
        self.assertEqual(chart_today, 9053)
        self.assertEqual(summary_today, chart_today)

    # ---------------- metric lain tidak berubah ----------------
    def test_other_metrics_unchanged(self):
        self._add_video(10, "111")
        self._add_snapshot(10, days_ago=1, views=1000)
        self._add_snapshot(10, days_ago=0, views=1500)

        self._add_video(1561, "1561")
        self._add_snapshot(1561, days_ago=4, views=51200)
        self._add_snapshot(1561, days_ago=3, views=69300)

        analytics = self._read()

        # Total Views = snapshot terakhir tiap video (immutable, tidak berubah).
        self.assertEqual(analytics["statistics"]["total_views"], 1500 + 69300)
        self.assertEqual(analytics["total_video"], 2)


if __name__ == "__main__":
    unittest.main()
