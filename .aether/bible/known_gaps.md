# bible:known_gaps
<!-- AETHER BIBLE (machine-readable). format=entry-v1. -->
<!-- Setiap entri dimulai dengan marker '## entry'. -->
<!-- Tambahkan knowledge lewat ProjectBrain/AETHER; jangan edit manual. -->

## entry
- id: 6b0e46ab4f154b8c90b2b8b80941890a
- source: ai
- confidence: 0.6
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Status semantics for other product statuses (e.g. 'failed', past-uploaded) were only touched in tests; full enumeration of statuses and their delete semantics is not documented."

## entry
- id: 58dca5bedd834ec2b5edb256e8b7693c
- source: consultant
- confidence: 1.0
- created_at: 2026-09-23T15:45:12.451932+00:00
- updated_at: 2026-09-23T15:45:12.451932+00:00
- content: "Pada mode QUICK, Project Map (.aether/map/atlas.json & rig.json) MISSING, sehingga atlas_query/rig_query tidak bisa dipakai dan isi source tidak dapat dibaca. Setiap analisis kode untuk project ini (termasuk bug video_analytics) memerlukan refresh/generate Project Map lalu mode Investigate agar tidak berspekulasi."

## entry
- id: ceb46c6430444572be5ffc4b6b1c02e4
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "No regression test was created for delete-immutability of daily analytics (intentionally, since no fix was needed per the stop instruction)."

## entry
- id: 8cf77bfbd9af4199aa6d86ebaa5a6bad
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "Existing test suite (tests/, including tests/test_creator_report_delete.py) cannot be executed in the current environment due to missing pymysql dependency."

## entry
- id: 6099fe83ce5540529c67dd85522c1eca
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "DB-level schema state (triggers, referential_constraints delete_rule) was not verified; only source-level absence of CASCADE was confirmed."

## entry
- id: a367df3542ee45eaa8f947afc7f4ae7d
- source: consultant
- confidence: 0.6
- created_at: 2026-09-23T16:17:33.267670+00:00
- updated_at: 2026-09-23T16:17:33.267670+00:00
- content: "Summary metric \"Perubahan hari ini (+X)\" di halaman /creator/<id>/video_analytics BELUM terpetakan di Bible: belum diketahui file/fungsi/SQL/dataset yang menghasilkannya. Kandidat kuat: angka summary (Total Video/Total Views/Avg/Median/Highest/Lowest + Perubahan hari ini) dihasilkan dari jalur _read_analytics di routers/creator/video_analytics.py (yang memakai LEFT JOIN upload_jobs/tiktok_products), sedangkan daily_views_chart dihasilkan dari jalur terpisah VideoAnalyticsService.get_creator_daily_views_chart() di includes/video_analytics/video_analytics.py. Dua jalur ini memakai dataset & fungsi agregasi yang berbeda, sehingga angka \"view hari ini\" pada summary dan titik hari ini pada chart dapat berbeda. Selisihnya belum terverifikasi."

## entry
- id: a833b37a355c463380cfd8ff3a65aebd
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Not verified: DB triggers and ON DELETE CASCADE behavior for analytics tables (out of scope for this divergence)."

## entry
- id: f9c0c9c665e94227a291b0d61e2b2e7a
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Verification ran against a live DB, so the exact numbers (887759 / 27177 / 9053) can drift over time; they matched the report exactly at observation time only."

## entry
- id: fdd5055aa6634f3cb7dc8b573c49d8b9
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "The fix is not implemented: no code change, no regression test, no schema change has been made yet. Proposed tests (fake DB, pattern from tests/test_creator_report_delete.py): (A) today+yesterday snapshot -> views_growth_today == chart today point; (B) stale curr (3 days old) -> contributes 0 to today but is booked on its own date; (C) negative delta clamps to 0; (D) invariant chart point(today) == total_views_growth_today."

## entry
- id: cf9997d6130147609f6012aa273fe3d3
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Videos beyond the max_videos = 90 capture limit may have no today snapshot by design; expanding capture is a separate task."

## entry
- id: 679d25de99bd4701b710e1afdb3d2d66
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "End-to-end scan for creator 2 could not be validated in this environment because `seleniumbase` is not installed."

## entry
- id: e1cd0fe11ec64144825c8473132c6886
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "No confirmation that the updated scan produces 195 snapshots; requires running scan in a proper environment."

## entry
- id: e83d36ac43df493bad2b1da709a2c322
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "The 104 missing snapshots from 2026-09-23 are a data coverage gap that the fix aims to prevent going forward."

## entry
- id: 6a51c295a30b40a3b73cd38be47fcffb
- source: consultant
- confidence: 0.8
- created_at: 2026-09-23T17:58:17.648518+00:00
- updated_at: 2026-09-23T17:58:17.648518+00:00
- content: "Belum terverifikasi: batas scroll & cap video pada jalur video_analytics. Diketahui max_videos=0 (unlimited) di dua jalur (router + scanner) dan _scroll_until_done scroll sampai STALL_LIMIT saat tanpa cap, tapi TIDAK dapat dikonfirmasi apakah loop scroll sudah punya counter iterasi, nilai STALL_LIMIT, apakah early-return berbasis hitungan video ada di dalam loop, mekanisme dedup (id TikTok vs pk), dan rantai pemanggilan pasti endpoint /creator/<creator_id>/video_analytics -> service -> scraper/scanner. Karena mode QUICK dan Project Map MISSING, isi source tidak dapat dibaca; perlu Investigate mode setelah refresh/generate Project Map sebelum menyimpulkan atau menulis kode."

## entry
- id: 88d61cc13bf3499b876610ca81929e3c
- source: ai
- confidence: 1.0
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Project Map (.aether/map/atlas.json & rig.json) is missing; analysis is based on direct source reading."

## entry
- id: 68dd8b3701014a00a56dbb96fe008ad5
- source: ai
- confidence: 0.7
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "No external configuration for MAX_SCROLLS or video cap; constants in scraper.py are sole source (assumption, needs confirmation)."

## entry
- id: ad5c54719a1f4c699c8958901ea51433
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Minimum scrolls needed to reach 190 videos on real TikTok profile unverified; 6 may be insufficient (TikTok loads ~16-24 videos per page)."

## entry
- id: 46321a28219844428121d87d261406d2
- source: ai
- confidence: 0.7
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Shape of api/post/item_list response per page (16-24 items) only observed from Chromium cache, not official contract."

## entry
- id: 066f075d748243f7ad8f3f6d7a2fe6f0
- source: ai
- confidence: 0.7
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Whether _count_links ever counted duplicate IDs (e.g., pinned) on real profiles unmeasured."

## entry
- id: 6a59bb2abca946119878a890bbaaa3b6
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Numeric equality of summary vs chart after cap 190 not verified on live data."

## entry
- id: 5dd908bf72974a40a7b723186c1fc268
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "seleniumbase not installed, limiting end-to-end validation with real browser."

## entry
- id: 59d807cb2ca8415ba374f6629824c915
- source: ai
- confidence: 0.75
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "No regression run possible for tests requiring flask/pymysql/cv2 in the current venv; those areas are unverified for this change."

## entry
- id: 26023718379544d9b190e2f1af464087
- source: ai
- confidence: 1.0
- created_at: 2026-10-04T05:51:01.878813+00:00
- updated_at: 2026-10-04T05:51:01.878813+00:00
- content: "No knowledge base exists for the underlying project: architecture, UI contracts, conventions, decisions, bugs, and gaps are all unobserved and must be re-derived from real work in future sessions."
