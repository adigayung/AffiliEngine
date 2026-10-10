# bible:known_bugs
<!-- AETHER BIBLE (machine-readable). format=entry-v1. -->
<!-- Setiap entri dimulai dengan marker '## entry'. -->
<!-- Tambahkan knowledge lewat ProjectBrain/AETHER; jangan edit manual. -->

## entry
- id: dd5332f6697143e399c9156fc67f4590
- source: consultant
- confidence: 0.5
- created_at: 2026-09-23T15:45:12.419811+00:00
- updated_at: 2026-09-23T15:45:12.419811+00:00
- content: "Laporan bug (belum diverifikasi, dari user): pada page /creator/<creator_id>/video_analytics, setelah sebuah product/job dihapus, data pada view harian dan grafik untuk hari-hari berikutnya tidak lagi sesuai dengan data asli hasil pengambilan pada hari itu. Berlaku untuk semua creator. Dugaan awal: metrik harian/grafik dihitung ulang (re-aggregate) dari state tabel job saat ini, sehingga penghapusan job menghapus kontribusi historis dan mengubah data hari-hari lampau (tidak ada snapshot harian yang immutable). Belum terbukti — butuh Investigate mode / akses source."

## entry
- id: 79c10445dbe4465fb802586f45aec61c
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Bug: 'Perubahan hari ini' summary badge != today's point on 'View Harian — 45 Hari Terakhir' chart for the same creator. Root cause: routers/creator/video_analytics.py:79 + includes/video_analytics/video_analytics.py:316/:394 use the two most recent snapshots per video with no date filter, whereas get_creator_daily_views_chart() (same file, ~655-695) uses latest-per-(video,date). Repro: creator_id=2 on 2026-09-23 => 27177 vs 9053; difference 18124, of which 18100 from video pk=1561."

## entry
- id: 2af43d27bc4e4afeb6ab645e3ed7366e
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Fixed: summary 'Perubahan Hari Ini' previously used views_growth = latest − previous without verifying the latest snapshot date was today, causing stale videos to inflate today's summary (e.g. 27177 instead of 9053)."

## entry
- id: 078c10f3831b4d50be222be0f85d7d9a
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Previously, `max_videos=90` in `routers/creator/video_analytics.py` caused only 90 videos to be processed, leaving 104 without snapshots."

## entry
- id: e9305016d27c485f89d6a772e96a88de
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Silent `except: continue` in `VideoAnalyticsService.update_creator_analytics` dropped processing failures without reporting."

## entry
- id: 88701951cf234f6daf3c5615364a9074
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "`ZeroDivisionError` would occur in scraper progress calculation when `max_videos` was set to a large sentinel (999999) or 0 in unlimited mode (fixed by adding unlimited branch)."

## entry
- id: 84359fcc0d854bfc9c24503a1de7f0df
- source: ai
- confidence: 1.0
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Bug: POST /creator/<creator_id>/video_analytics/update triggers unlimited scrolling (max_videos=0) causing performance degradation and potential hang."

## entry
- id: 63a7e10f556a498a9220494f9843dbad
- source: ai
- confidence: 1.0
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Bug: In unlimited mode, _scroll_until_done runs up to MAX_SCROLLS=500 with no early stop based on video count."
