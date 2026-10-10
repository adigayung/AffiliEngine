# bible:facts
<!-- AETHER BIBLE (machine-readable). format=entry-v1. -->
<!-- Setiap entri dimulai dengan marker '## entry'. -->
<!-- Tambahkan knowledge lewat ProjectBrain/AETHER; jangan edit manual. -->

## entry
- id: 0d81485369c2406697deacbfefefaf17
- source: ai
- confidence: 0.95
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Status 'scheduled' is a derived/display status: DB column status='uploaded' AND schedule_datetime > NOW(). Computed by `_compute_display_status` in routers/creator/report.py, with related logic in includes/production_monitor.py."

## entry
- id: 715c0fe72f4545718e6222d48dd74f18
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Status 'pending' corresponds to DB column status='pending'."

## entry
- id: 868f1792bd5142d8a74e655a81c4b861
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "routers/creator/report.py functions involved: `_compute_display_status`, `_parse_datetime` (new helper), `_bulk_delete_scheduled_jobs` (new), `bulk_delete_upload_jobs` (extended), `_bulk_delete_pending_jobs` (unchanged), `_delete_job_folders`, `remove_schedule` (updated for scheduled)."

## entry
- id: 7e8a8e3543ba48e892eb9d70fda9bee1
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "`_bulk_delete_scheduled_jobs()` deletes only DB records for rows uploaded + schedule_datetime > now, never calls shutil.rmtree or touches the filesystem, and cleans up empty `schedule_batches` rows (DB-only, no disk changes)."

## entry
- id: f7fd92bd94f74cad806fe0e578266975
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "New test file tests/test_creator_report_delete.py contains 9 tests, all passing, using a fake DB and `FakeShutil` to assert scheduled deletes touch no files while pending deletes still remove folders."

## entry
- id: 7538dd9c64c849609767fd8fe9e84159
- source: ai
- confidence: 0.85
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Project venv does not contain Flask or pymysql; tests were run with C:\\Users\\...\\Python310\\python.exe which has Flask, with pymysql installed there."

## entry
- id: 260194bbe1564ec98c8c85479f3de783
- source: ai
- confidence: 0.85
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Validation performed: py_compile OK for report.py and the test, Jinja parse OK for creator/report.html, 9/9 unit tests pass."

## entry
- id: abc2c5f55b7d4d009ac1be2f578f0533
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "Daily chart query (includes/video_analytics/video_analytics.py ~655-695): takes latest snapshot per (video_id, date) via dedup from tiktok_video_stats JOIN tiktok_videos v ON s.video_id = v.id WHERE v.creator_id = %s; baseline = last snapshot before start_date per video; daily_view(video, D) = max(0, views(latest D) - views(previous observation))."

## entry
- id: a86beab050e64adfbed7ae20e0cf4282
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "The daily chart query contains no join to upload_jobs or tiktok_products; only the video list label uses LEFT JOIN upload_jobs/tiktok_products (_read_analytics)."

## entry
- id: d94b29152e19475ba337c66f14345174
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "Repo-wide INSERT INTO tiktok_video_stats occurs at exactly one location (includes/mysql.py:1210); UPDATE tiktok_video_stats at exactly one location (includes/mysql.py:1197)."

## entry
- id: f10ee7eaf9844303a0dfda22f256d79c
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "Only three DELETE FROM statements exist in source (creators, tiktok_shopee_products, shopee_products); there is no DELETE/TRUNCATE against tiktok_videos or tiktok_video_stats."

## entry
- id: cfa87763417441c086289e04cf2de049
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "No ON DELETE CASCADE found in source; includes/video_performance/migration.sql only does ALTER TABLE ... ADD COLUMN/INDEX."

## entry
- id: bbb737563cec440892479a7c77ba9bbd
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "python -m py_compile on includes/video_analytics/video_analytics.py, routers/creator/video_analytics.py, routers/creator/report.py returned OK."

## entry
- id: 6ab66c0ae92a43a2ba11d0a81ddcd447
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "python -m pytest tests -q fails at collection with ModuleNotFoundError: No module named 'pymysql'; requirements.txt lists pymysql (environment issue, not a code regression)."

## entry
- id: 2a3318493dfd4fdd89bfb67c6a4b36a2
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "Project Map files .aether/map/atlas.json and rig.json are MISSING; Atlas/RIG engine files J:\\CODE_ATLAS\\atlas.py and J:\\MAP_CODE_RIG\\rig.py do not exist."

## entry
- id: 2e59ae7b6e0f46ce91d2bcacbb13cf75
- source: ai
- confidence: 0.7
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "QUICK mode cannot read source (as reported); source verification had to use read_file/search_code directly."

## entry
- id: 6e607de8db074906b08932c6f2f9a54b
- source: ai
- confidence: 0.7
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "tests/test_creator_report_delete.py contains 9 tests (baseline currently not runnable in the active venv)."

## entry
- id: 335a6aa6d066414f9817922509e8a506
- source: consultant
- confidence: 0.95
- created_at: 2026-09-23T16:18:40.744337+00:00
- updated_at: 2026-09-23T16:18:40.744337+00:00
- content: "Kasus divergensi \"view hari ini\" (summary vs chart Video Analytics) dipersempit ke creator konkret: \"Kang Petruk\" creator_id=2. Angka laporan: summary \"Perubahan hari ini\" = +27.177; titik hari ini pada chart \"View Harian — 45 Hari Terakhir\" = 9.053; selisih = 18.124. Summary contoh: Total Video 195, Total Views 887.759, Avg 4.552, Median 799, Highest 191.100, Lowest 0. Validasi harus pakai filter creator_id=2 dan (bila memungkinkan) menampilkan kontribusi delta per-video hari ini untuk melihat video mana yang masuk summary tapi tidak ke chart (atau sebaliknya). BELUM TERVERIFIKASI: mode QUICK + Project Map (.aether/map/atlas.json & rig.json) tetap MISSING, sehingga source tidak bisa dibaca."

## entry
- id: f366e0ab2f1b4d0daa31e331621bcb5a
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Summary growth formula: total_views_growth = sum(v.get('views_growth', 0) or 0 for v in videos) at routers/creator/video_analytics.py:79; per-video views_growth = views - prev.get('views', views) if prev else 0 at includes/video_analytics/video_analytics.py:394."

## entry
- id: 38af01a26a594660b2e7d4127f8b5a0d
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Summary 'two latest snapshots' query at includes/video_analytics/video_analytics.py:316 uses ROW_NUMBER() OVER (PARTITION BY video_id ORDER BY snapshot_time DESC) with latest.rn <= 2 and has NO WHERE DATE(snapshot_time)=CURDATE() filter, so 'prev' may be days/weeks old."

## entry
- id: 0cee48528f9d440e8d351ca89afc1324
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Chart logic: dedup latest snapshot per (video_id, DATE) within the 45-day window; baseline = last snapshot before the window per video; daily delta per video = max(0, cur - previous observation); total_delta_map[d] = sum of deltas across videos for date d."

## entry
- id: 051cb4c09b154b3eace0fc2aa5501b9d
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Reconstruction for creator_id=2 (2026-09-23): total_views=887759, total_views_growth=27177, today component=9053 (91 videos with snapshot TODAY), stale component=18124 (104 videos with curr != TODAY). 18100 of the 18124 comes from a single video pk=1561 (tiktok id 7682446872346201362)."

## entry
- id: b1768f8d47f54a1ab45ab3dd83f7ec4d
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Video pk=1561 moved 51200 -> 69300 on 2026-09-20 (growth 18100) and was not re-scanned 09-21..09-23, so its delta keeps being reported as 'today' by the summary while the chart correctly books it on 2026-09-20."

## entry
- id: 3cad6de14c9247cab17b8525d7d4d5e3
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Chart series (creator_id=2): 2026-09-20 -> 36489, 2026-09-21 -> 11575, 2026-09-22 -> 33592, 2026-09-23 -> 9053 (matches reported 'today' point)."

## entry
- id: 5237ab4255c24fdebeda934688cf9eda
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Daily capture is capped at 90 videos: routers/creator/video_analytics.py:40 max_videos = 90 and includes/tiktok_scrape_videos/scraper.py:305-306 self.videos = self.videos[:self.max_videos]. Creator 2 has 195 videos, so only ~91-93 are captured per day; oldest stale curr snapshot observed is 2026-08-19."

## entry
- id: d9cc9f6a81944408b47e3a579815c9ac
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Timezone is not a factor: @@global.time_zone / @@session.time_zone = SYSTEM, NOW()/CURDATE() = 2026-09-23, and Python datetime.now() is local — both paths agree on the day boundary."

## entry
- id: 6436dca83438425482b3bd76d3995ee5
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "No negative deltas exist for the case (sum of negative deltas = 0), so max(0, Δ) clamping is irrelevant to this divergence. All 195/195 videos join successfully between tiktok_videos and tiktok_video_stats."

## entry
- id: 8a9da7f5284646f4914ae9f65ff8dde8
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Local DB used for verification: 127.0.0.1/tiktok_affiliate_analyse per config/database.json, queried read-only (SELECT only); observations taken 2026-09-23 23:23."

## entry
- id: 9d32e0ab78c740759bbd3a2a5a632946
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "creator_id = 2 (Kang Petruk) has 195 videos; scraper max_videos = 90 means only part of the catalog can have same-day snapshots."

## entry
- id: 94471249310242baac1a6fcfb81b2baa
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Bug numbers: summary today was 27177, chart today was 9053; 27177 = 9053 + 18124."

## entry
- id: da58119120fc4eceb8b74268d2750c39
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Stale video_pk = 1561 (TikTok 7682446872346201362) had snapshots 2026-09-19 = 51200, 2026-09-20 = 69300, no later snapshot; growth +18100."

## entry
- id: c5c9a10ef1964e4689d316b31de072d9
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Validation on live MySQL for creator_id=2 after fix: summary_today = 9053, chart_today = 9053, MATCH = True."

## entry
- id: 36312e912c4842ecaedffdb6c9ff3ec0
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "8 stale videos with growth contributed 18124 total (top: pk=1561 → 18100)."

## entry
- id: ad5053a5a7ad4c64905003d297cc39c9
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Chart last 5 points validated: ('2026-09-20', 36489), ('2026-09-21', 11575), ('2026-09-22', 33592), ('2026-09-23', 9053)."

## entry
- id: fb6f495a559d4a6d97df112454e47b16
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Test run: python -m unittest discover -s tests -v → Ran 18 tests, OK (9 new regression tests + 9 existing)."

## entry
- id: 235fb6d9357342dda68bc4733b0cc59a
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "pymysql installed into venv per requirements.txt to run the suite (environment change, not repo change)."

## entry
- id: 7d22f4de7d7140f790ccd3595dcbb57f
- source: ai
- confidence: 0.75
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Repo contained pre-existing uncommitted changes in report.py, report.html, workflows_*.py, images.txt, unrelated to this task."

## entry
- id: 19099532cee449bb8436f1cda61368e8
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Creator ID 2 corresponds to 'Kang Petruk'."

## entry
- id: d38278800da6425ea653960da490aee6
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Database had 195 videos for creator 2."

## entry
- id: f113c17f1ba04f809269366fb59dacbc
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Snapshot on 2026-09-23 contained 91 videos; 104 videos were missing that day."

## entry
- id: e093bff57acb4f0fb67e3cc08598de75
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "The hardcoded cap causing the issue was `max_videos = 90` at `routers/creator/video_analytics.py:40`."

## entry
- id: 600ee78fec434c7b89ebfc0fe6ee903a
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Another cap was `max_videos=max(20, scroll_count*10)` at `includes/video_performance/scanner.py:58 & :82`."

## entry
- id: 96e52f455c6a4d39a6db00683a78101e
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "The scraper's `_merge` method had `self.videos = self.videos[:self.max_videos]`; now it slices only if `max_videos > 0`."

## entry
- id: f26408bf01cc4955876bef03d3306d43
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "The scraper uses `STALL_LIMIT` to stop scrolling when no new videos load."

## entry
- id: 8ca8729575494a28a393abd3d573ba7a
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "`tiktok_video_stats` table stores video snapshots."

## entry
- id: 32738876c91a4277b10dcbca8d82f026
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "After fix, test suite: 34 tests total (18 old + 16 new), all pass."

## entry
- id: 1e7e308f1e2c461dab85eb031a836321
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Environment lacks `seleniumbase` module, so live scan could not be executed in the session."

## entry
- id: 4628db323cc14a0fb1dbd39f162abbea
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "DB time at validation: 2026-09-24 00:02."

## entry
- id: a91d7e03bd794e63b4cf585ae3030562
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Changed files: `includes/tiktok_scrape_videos/scraper.py`, `routers/creator/video_analytics.py`, `includes/video_analytics/video_analytics.py`, `includes/video_performance/scanner.py`, and new test file `tests/test_video_analytics_scan_coverage.py`."

## entry
- id: 2c3af90203d04fb5b7fb9f9be31a8707
- source: ai
- confidence: 1.0
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "routers/creator/video_analytics.py:44 sets max_videos = 0 and passes to update_creator_analytics."

## entry
- id: 21116c3f95674b97bc7c398c5750b10e
- source: ai
- confidence: 1.0
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "includes/video_performance/scanner.py:65 and :91 create TikTokScraper with max_videos=0."

## entry
- id: a8545173f7a14030a98d9f2b8ea41fcd
- source: ai
- confidence: 1.0
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "includes/tiktok_scrape_videos/scraper.py:36 defines UNLIMITED_VIDEOS = 0; __init__ (lines 80-88) sets self.unlimited = (max_videos == UNLIMITED_VIDEOS)."

## entry
- id: 6cf7f39e8aae4a9d8a14cbe70b64dfbb
- source: ai
- confidence: 1.0
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "scraper.py:32 defines MAX_SCROLLS = 500; _scroll_until_done uses max_scrolls = MAX_SCROLLS when self.unlimited (line 233), and only checks video target when not unlimited (line 240)."

## entry
- id: 75ee313417944445a7a4d26d4a823f98
- source: ai
- confidence: 1.0
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "scraper.py:27 defines STALL_LIMIT = 8; _scroll_until_done stops if self._stalled >= STALL_LIMIT."

## entry
- id: 546f6293d6784a8a9873659ef08eb0be
- source: ai
- confidence: 1.0
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "scraper.py _merge (lines ~320-355) applies cap only if not self.unlimited (line 334)."

## entry
- id: 0671141285e841a488aa7e2abc79f991
- source: ai
- confidence: 1.0
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "JS_GET_ID_ORDER (scraper.py:40-50) returns unique video IDs from DOM (dedup by id)."

## entry
- id: 8903a8cd2f79459db3960bf66c477b35
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "_count_links (scraper.py:219-224) counts anchor elements, not unique videos."

## entry
- id: a4c81c1fa2514fd0ac9be568ea16f4da
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "tests/test_video_analytics_scan_coverage.py has 16 tests, currently all passing, and locks in unlimited behavior (e.g., test_default_is_unlimited, test_merge_processes_all_fetched_videos)."

## entry
- id: 3a83d81471014e129f85254cd05890f7
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "git diff HEAD~3 shows changes: router max_videos=90 -> 0; scanner max_videos=max(20, scroll_count*10) -> 0; scraper max_videos = ... else UNLIMITED_VIDEOS and max_scrolls = min(500, max_videos*2+5) if max_videos != 999999 else 500 -> unlimited branch."

## entry
- id: da0fffe521ac414dbbb2782e9984adbb
- source: ai
- confidence: 0.7
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "No external configuration (env/config) found for MAX_SCROLLS or video cap; constants in scraper.py are sole source of truth (assumption, needs confirmation)."

## entry
- id: c87939fc11c94f9da9e4f4bb8b2d9d07
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "seleniumbase dependency not installed in current environment, so full end-to-end scan cannot be run."

## entry
- id: 4a0def6494534540a5a8e252b4e43b8f
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "creator_id=2 (Kang Petruk) has 195 videos, exceeding proposed cap 190."

## entry
- id: 119c7a3b0af44ef7945962cef51eaade
- source: ai
- confidence: 0.85
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Normalization uses ffmpeg loudness targeting to -14.0 LUFS (observed E2E log: `[OK] Normalize audio: -45.8 LUFS -> -14.0 LUFS`)."

## entry
- id: b46a49859df24237bd6464880fc8f2a1
- source: ai
- confidence: 0.95
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "New test file tests/test_video_pipeline_normalize_audio.py contains 28 tests and all pass (`python -m unittest tests.test_video_pipeline_normalize_audio` -> Ran 28 tests, OK)."

## entry
- id: 96ce6b1ad8c9473597dce45465c3607c
- source: ai
- confidence: 0.95
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Normalization only has an effect when the decoded file has audio (i.e. preserve_audio active); when a file has no audio, normalize_video_file() returns None and the step is skipped with a [SKIP] log (not an error)."

## entry
- id: 1a6db9dffcee4d82a8747a67ac048bf5
- source: ai
- confidence: 0.9
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "audio_normalize.py previously ran only as a CLI script and was not invoked by the pipeline before this change."

## entry
- id: 3268ee510bee4d28b9285733012f57a3
- source: ai
- confidence: 0.8
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Version control: audio_normalize.py's `--help` CLI still works after refactor; CLI exit-1 behavior preserved."

## entry
- id: 83fea81495f24e468b52e2acc30a689f
- source: ai
- confidence: 1.0
- created_at: 2026-10-04T05:51:01.878813+00:00
- updated_at: 2026-10-04T05:51:01.878813+00:00
- content: "Observations contain a single trivial exchange: prompt instructed a pure greeting response; the result was exactly 'hallo'."

## entry
- id: bd22c5126d8a4db3b1c6a64ff019cf2a
- source: ai
- confidence: 1.0
- created_at: 2026-10-04T05:51:01.878813+00:00
- updated_at: 2026-10-04T05:51:01.878813+00:00
- content: "No project name, repository, language, framework, or codebase context is present in these observations."

## entry
- id: 4e4ef39d711e4404a6902de42d95d62d
- source: ai
- confidence: 1.0
- created_at: 2026-10-04T05:51:01.878813+00:00
- updated_at: 2026-10-04T05:51:01.878813+00:00
- content: "No files were read and no code was produced during this session."

## entry
- id: 7d38a49e8a1c467e90920c4f0c35e09f
- source: consultant
- confidence: 0.9
- created_at: 2026-10-10T15:46:09.348877+00:00
- updated_at: 2026-10-10T15:46:09.348877+00:00
- content: "Kontrak submit per schedule_mode pada halaman jadwal (dibaca UploadScheduler.__init__, includes/schedule/scheduler.py:52-174): interval -> start_time + interval_hour; fixed -> upload_times (JSON array HH:MM); weekly -> weekly_schedule (JSON object day->[times], day keys Monday..Sunday); pattern -> pattern (JSON array stage {duration, unit:[days|weeks|months|until_finish], strategy:[interval|fixed|weekly], config:{interval_hour,interval_minute | times:[...] | schedule:{...}}}); import_schedule -> import_pattern + import_times. Semua mode juga mengirim products, distribution_method, upload_directory, start_date. Endpoint: POST /product_list/prepare_upload/buat_jadwal."

## entry
- id: 8e81826a36694994ae1336dc02b988e2
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Shared helpers added in prepare_jadwal.html: downloadScheduleSettings(method, config), showTabForMethod(method), applyScheduleSettings(data) (returns false for unknown method)."

## entry
- id: d81ca2101eec4e8188d0535b526dd86a
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Each method tab added get<Method>SaveConfig(), save<Method>Settings(), apply<Method>Settings(cfg); import tab detected via analyzeImportFile()."

## entry
- id: bc6e4374f868488b884f81c6c341fe02
- source: ai
- confidence: 0.9
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Verification included: Jinja parsing of all 6 templates OK; node --check on combined rendered JS OK; Node stub-DOM round-trip tests for Save/Load of all 4 methods (correct JSON fields, no upload_directory/start_date, tab auto-switch, radio restored); new-format import triggers no fetch, legacy 'folders' import still fetches import_analyze once; project unit suite passes 70 tests."

## entry
- id: b6d0f25b435341c2a14370ab99790b82
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Pre-fix HEAD behavior: calling Save raised 'ReferenceError: saveFixedSettings is not defined' and every upload_schedule_settings file was rejected with alert 'Format file tidak valid. File harus memiliki key \"folders\" berupa array.' — the Save/Load block was never present in the rendered page, so the new-format path had no callable target."

## entry
- id: 21434030e07742fc8828beebbaf7eb23
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "The reported schema mismatch hypothesis was disproven: Save writes config.upload_times and apply reads cfg.upload_times; tab selector a[href=\"#tab-fixed\"] exists and maps to SCHEDULE_METHOD_TABS.fixed."

## entry
- id: 23a196311a204bba8f4f2d2d210906fc
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Fix covered 6 templates; no router, DB, or endpoint changes; file format schema unchanged (type/version/distribution_method/method/config) with only read-side tolerance added."

## entry
- id: 1d309c5d6aa04f6ab8dd7a2888695519
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "E2E Playwright headless against a stdlib server rendering the real templates + Bootstrap CDN: 34/34 checks passed covering AC-1..AC-7."

## entry
- id: aece22ec7b044c528e205d9768919fce
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Negative control (same harness on HEAD) produced 17 failing checks, confirming the tests detect the root cause."

## entry
- id: 614497b76363485b8ecd90ef286801dc
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "node --check passed on all inline <script> blocks (6 templates) and Jinja parse+render succeeded; project test suite reported 70 passed plus 6 subtests."

## entry
- id: 6ff065bb6d6a493195145764741e9e8a
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Legacy-format files (containing 'folders') still make exactly one POST to /product_list/prepare_upload/import_analyze and show the Pattern Editor."

## entry
- id: eeb48592a47d4e27bb1507aa9a1ce8a9
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "New-format load issues no network requests."
