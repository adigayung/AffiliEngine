# bible:problems
<!-- AETHER BIBLE (machine-readable). format=entry-v1. -->
<!-- Setiap entri dimulai dengan marker '## entry'. -->
<!-- Tambahkan knowledge lewat ProjectBrain/AETHER; jangan edit manual. -->

## entry
- id: 562ff4631f4d474fa6a551d7ea8ded7d
- source: ai
- confidence: 0.8
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Project venv lacks Flask and pymysql, so running tests/checks requires an alternate interpreter (system Python310); dependency/venv setup may be inconsistent."

## entry
- id: db32958ba83741078363ff176150d596
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "Cannot run the repo test suite because pymysql is not installed in the active venv, blocking regression verification."

## entry
- id: 7a49133f964043d8ae7268ced501f4cb
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "Project Map/Atlas artifacts are missing, preventing quick navigation and requiring manual source reading."

## entry
- id: 7e416f47aa6643c0973e0541e42bec9c
- source: ai
- confidence: 0.75
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "The reported symptom could actually be observed on the report page listing rather than the video_analytics chart; it needs confirmation (before/after screenshots of #dailyViewsChart and DB queries)."

## entry
- id: 80c4505bf1be4df9bd661fbeafddeb50
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "DB-level triggers or FK ON DELETE CASCADE for analytics tables cannot be verified from source; SQL inspection queries were provided to check."

## entry
- id: 6e42418b32584c6493c54c2004cf360d
- source: consultant
- confidence: 0.9
- created_at: 2026-09-23T16:17:33.295497+00:00
- updated_at: 2026-09-23T16:17:33.295497+00:00
- content: "Laporan user: pada /creator/<id>/video_analytics, summary \"Perubahan hari ini\" = +27.177 sedangkan titik hari ini pada chart \"View Harian - 45 Hari Terakhir\" = 9.053 (selisih 18.124). Belum terverifikasi: tidak dapat direkonstruksi di mode QUICK karena Project Map (.aether/map/atlas.json & rig.json) MISSING (atlas_query/rig_query error) dan mode ini tidak boleh membaca source. Perlu mode Investigate untuk membaca routers/creator/video_analytics.py (_read_analytics + jalur summary) dan includes/video_analytics/video_analytics.py (get_creator_daily_views_chart, query ~655-695) lalu membandingkan dataset, filter tanggal/timezone, definisi baseline/delta, dan dedup snapshot kedua jalur."

## entry
- id: 85fc39ab85cc4288a0cb2bb8cddbaba5
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Summary 'Perubahan hari ini' is retroactively sticky: stale videos (not captured today) keep contributing their old multi-day delta to a metric labeled 'today'. For creator_id=2 this inflated the metric from 9053 to 27177."

## entry
- id: 219fc9059c2245a59ac4fc95ceabb648
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Only ~91-93 of creator 2's 195 videos are captured per day due to max_videos=90, guaranteeing a persistent stale-video population and a structural gap between summary and chart."

## entry
- id: 6bec7337078a46c0b7c75822ed2a61b5
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: ".aether/map (Project Map) is missing, forcing manual file discovery during investigation."

## entry
- id: 48fe99fb79c7492aa363552a4c2753da
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Labeling is ambiguous in the UI: 'Perubahan hari ini' can mean either today-dated delta or last-snapshot delta; both interpretations currently coexist in one dashboard."

## entry
- id: ae80f117197d43b386f702cfb9e64d3a
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "max_videos = 90 is smaller than creator_id=2's 195 videos, so some videos may lack a today snapshot (already present but out of scope for this fix)."

## entry
- id: bc75d5b452b640b48d1b40d1d0491dde
- source: ai
- confidence: 0.7
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Repo working tree has unrelated uncommitted changes (report.py, report.html, workflows, images.txt) that could confuse diffs."

## entry
- id: ece52f1aeb364ff2b3d8f48a686a8d52
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Before fix, 104 of 195 videos for creator 2 were not processed due to `max_videos=90` cap."

## entry
- id: 763f3569e4e748929a65fd4e071fd29e
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Failure handling in `update_creator_analytics` silently discarded failures (`except: continue`) without counting or logging."

## entry
- id: de28112d850d43ceb11cca6dcd44fdfb
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "The cap was duplicated in two independent scan paths (router and performance scanner), risking inconsistent behavior."

## entry
- id: b3c3f67702e9493abe4af0ff89fe5b20
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "The progress calculation in unlimited mode would raise `ZeroDivisionError` (caught by tests during fix)."

## entry
- id: d4143a7c6de049e6b9a41c3336baba82
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Live scan could not be executed in the session due to missing `seleniumbase` module; validation pending."

## entry
- id: d51f3af799584835a04494d1d2f615d3
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "`latest_snapshot_today` is 0 because scan not yet run after fix."

## entry
- id: a31d4e0a26184eebb622d26fef57294a
- source: consultant
- confidence: 0.7
- created_at: 2026-09-23T17:58:17.587932+00:00
- updated_at: 2026-09-23T17:58:17.587932+00:00
- content: "Laporan user (issue baru, belum diverifikasi di source): endpoint /creator/<creator_id>/video_analytics melakukan infinite/unlimited scrolling sehingga scraper menemukan ratusan/ribuan video, proses sangat lama, dan browser/agent dapat hang. Requirement user: (a) batas scroll tegas ~6-8 kali; (b) hard cap maksimal 190 video diproses/disimpan per creator; (c) stop segera saat 190 tercapai; (d) stop saat batas scroll tercapai; (e) jangan pakai max_videos=0 (unlimited) sebagai perilaku normal; (f) SEMUA jalur (router video_analytics + VideoPerformanceScanner) harus tunduk pada batas; (g) batas di level scraper/scroll, bukan slice post-scraping; (h) jangan ubah fitur analytics lain; (i) pertahankan storage/read analytics. Root cause kandidat (dari Bible terverifikasi): max_videos diset 0 di routers/creator/video_analytics.py (~40) dan includes/video_performance/scanner.py (~58 & 82), plus _scroll_until_done di includes/tiktok_scrape_videos/scraper.py dimodifikasi scroll sampai STALL_LIMIT saat tanpa cap eksplisit -> tidak ada batas jumlah scroll. Ini adalah PEMBALIKAN keputusan sebelumnya (yang mengubah 90 -> 0 unlimited) dan bertentangan dengan konvensi lama '0 = unlimited' / 'jangan hardcoded cap' untuk jalur ini. BELUM TERVERIFIKASI karena mode QUICK + Project Map (.aether/map/atlas.json & rig.json) MISSING -> isi source, nomor baris, isi _scroll_until_done, STALL_LIMIT, dedup, dan rantai pemanggilan tidak dapat dibaca. Perlu mode Investigate setelah generate Project Map."

## entry
- id: 083bf42ff3314d809d87760fb72bf973
- source: ai
- confidence: 1.0
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Infinite/unlimited scrolling in video analytics scan causes hundreds/thousands of videos to be processed, leading to long runtimes, potential browser/agent hang, and wasted resources."

## entry
- id: dded6adfc00f4a7aaa4da7f81e6c406d
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Risk: If cap only applied in scroll loop based on DOM count, videos added from API in _merge can exceed 190, bypassing the cap."

## entry
- id: 36b6b26ce32149e88dcbe032a011e34c
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Risk: Existing tests (test_video_analytics_scan_coverage.py) assert unlimited behavior and will fail/need revision when cap is introduced."

## entry
- id: 6c36ede47f794896bb23ea04f2858cdc
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Risk: Changing _count_links to unique count may break tests using FakeDriver that returns raw numbers."

## entry
- id: 309580601ec7423c9c45a96439541250
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Risk: CAPTCHA handling path (scan_with_captcha_awareness) might be affected by cap changes; must verify."

## entry
- id: ce179b15b6694ab1a057b34affb527e3
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Risk: Numeric consistency between summary 'Perubahan Hari Ini' and chart 'View Harian' after cap needs re-validation."

## entry
- id: 6757d574116e46b4b653448581c7093d
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Issue: No scheduler/cron; scans only triggered manually via UI, limiting scope but also meaning no background jobs."

## entry
- id: 4d21476cbb75466ca10e032cb1dbf8d9
- source: ai
- confidence: 0.85
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Venv is missing flask, pymysql, and cv2, so tests test_creator_report_delete and test_video_analytics_* cannot be imported/run — this pre-exists the change and is not a regression."

## entry
- id: 618b4f64df3f4fa19260a397245ae01a
- source: ai
- confidence: 0.7
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Default-flag inconsistency between PipelineRunner (True) and processor (False) could cause confusion if called directly; behavior depends on the caller path."

## entry
- id: c4b773951c3a45e5a4d4e135eb4191f8
- source: ai
- confidence: 1.0
- created_at: 2026-10-04T05:51:01.878813+00:00
- updated_at: 2026-10-04T05:51:01.878813+00:00
- content: "The observation set provides zero recoverable project knowledge, so any durable extraction about a software system is impossible from this source."
