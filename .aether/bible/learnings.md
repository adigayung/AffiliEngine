# bible:learnings
<!-- AETHER BIBLE (machine-readable). format=entry-v1. -->
<!-- Setiap entri dimulai dengan marker '## entry'. -->
<!-- Tambahkan knowledge lewat ProjectBrain/AETHER; jangan edit manual. -->

## entry
- id: 23c8887af1cc4f47bb106eceeac04f2e
- source: ai
- confidence: 0.95
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "'scheduled' is not a DB status column value; it is a computed status (uploaded + future schedule_datetime). Any logic keyed on 'scheduled' must use the derived computation, not a raw column check."

## entry
- id: 90b0583640a1452bbef99ce9223f4e01
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "The pending bulk delete endpoint also deletes folders via `_delete_job_folders()` when delete_folders=true; this side effect must be explicitly bounded to pending to avoid filesystem deletions for scheduled."

## entry
- id: eb54e51eff30483d9c66159dcb2619c7
- source: ai
- confidence: 0.85
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Tests use FakeShutil to assert filesystem operations are never invoked for scheduled deletes — an effective pattern for verifying 'no file deletion' requirements."

## entry
- id: b64bc470d7924aaba1c3019bbc0aee3f
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "The report page's per-date schedule listing is re-derived live from upload_jobs, so deleting one job removes it from past dates there — that is by-design for a schedule listing, and is a likely source of confusion with the immutable analytics chart."

## entry
- id: e802719500674808a5c6e498d15dea7a
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "The chart's delta algorithm uses a baseline snapshot before the 45-day window for the first in-window day; when the window shifts daily plus snapshot gaps exist, the leftmost point's value can vary slightly. This is a window/gap effect and is unrelated to product deletion."

## entry
- id: 3e46902670584cbcaa7a4428f9173742
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "When Project Map/Atlas is unavailable, verify by direct file reading (read_file/search_code) rather than assuming paths."

## entry
- id: cd959bcaa8134851a230ee4371e1ec20
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "Distinguish analytics metrics (snapshot-based, immutable) from schedule listings (live-aggregated from upload_jobs) when triaging 'historical data changed after delete' reports."

## entry
- id: 5ab67637c063410a8728a64a2e4a87cc
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Divergence between summary and chart stems from two different definitions of 'today': summary = two latest snapshots per video regardless of date (multi-day cumulative growth mislabeled as today); chart = latest-per-(video, DATE) with the point only populated for videos actually snapshotted that date."

## entry
- id: 2a1015f157504bdf8efa8d1eba48e4da
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "When debugging 'same metric, different numbers' issues, first classify hypotheses into dataset / timezone / baseline-delta semantics / clamping / JOIN-loss. Here H3 (baseline-delta definition) was the cause; H1, H2, H4, H5 were ruled out with evidence."

## entry
- id: 61393c79e1f545c5bcf7ca7dcfb98bd2
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "A per-video capture cap (max_videos) silently creates 'stale' videos whose last snapshot is arbitrarily old; any metric that ignores snapshot date will drifts systematically from any per-date metric. Expect the gap to scale with creator video count vs cap."

## entry
- id: ef22253affa54711b01edaad21748b9d
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Reproduce both numbers exactly with SQL before naming a root cause: build a CTE that mimics the app path (ROW_NUMBER rn<=2 vs latest-per-date + LAG) and compare SUM components, rather than reading code only."

## entry
- id: 621881459e3844279aa4df7a4c02e34d
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Chart semantics: growth booked per (video, date) using latest-per-date snapshot and max(0, Δ); summary must mirror that exact date semantics to stay in sync."

## entry
- id: 76ae6eda783e460880754c0c98e4874a
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "A video with a stale last snapshot can still legitimately appear on its own snapshot date in the daily chart, so it must not be dropped globally—only excluded from 'today'."

## entry
- id: 15107972b555453c9129a00c9b7fa37e
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Indicators like 'Total Views/Avg/Median/Highest/Lowest' derive from the latest snapshot and were not affected by this date-filtering bug."

## entry
- id: 5b5141f5600847eca2d53c2092a9e79d
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Regression test strategy: use a fake DB mimicking SQL service semantics to test today/stale/negative-delta/invariant cases."

## entry
- id: 911b82f076f544efae38caace1e8ac20
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Artificial caps can exist in multiple layers (router, service, scanner, scraper slicing) and must all be audited."

## entry
- id: 07a1623a53af4408a4d278bf49a6ce71
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Using a magic sentinel like `999999` to mean 'unlimited' is error-prone; it caused a `ZeroDivisionError` in progress calculation when `max_videos` was large."

## entry
- id: 9defa553fee34f3fb4fcc727c4e44b2e
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Silent `except: continue` hides processing failures; adding counters and logging reveals coverage gaps."

## entry
- id: 4d7949847fef4a6bb8cfd7c911b3e522
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Removing caps requires ensuring natural pagination/scroll termination (e.g., `STALL_LIMIT`) works correctly."

## entry
- id: 68fb8b259e1c4346aa307c87e2b4b0a3
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Regression tests for coverage should be independent of specific counts (test 195, 220, 87) and verify no slicing."

## entry
- id: 4aa34bee406c44fbbccf5171bf3596b7
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Live scan validation requires `seleniumbase` and Chromium; missing dependency blocks end-to-end testing."

## entry
- id: 1264984908d7481e81412796e78701ea
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "Unlimited scrolling is caused by two layers: callers passing max_videos=0 and scraper interpreting 0 as unlimited with MAX_SCROLLS=500; to fix, both layers must be changed."

## entry
- id: 44b5f611dd9d465b84a281328b953ca8
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "A hard cap must be enforced during collection (scroll loop) to stop browser early, and also defensively before DB insert because _merge can add API-only videos not seen in DOM."

## entry
- id: 9a9e7f994d6d4b97a89ec62ff7b52115
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "Counting unique videos requires using JS_GET_ID_ORDER (dedup by id) or equivalent; _count_links counts DOM anchors and may include duplicates (e.g., pinned videos)."

## entry
- id: 3b469e9d148f4660b3aa699aff26e62f
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Existing tests encode the old unlimited behavior and must be revised, not just added to."

## entry
- id: 35e8b54896e4464fbb92e6e7fc37e691
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "Reachability of 190 videos within 6 scrolls is uncertain; TikTok loads ~16-24 videos per page, so 6 scrolls might not reach 190."

## entry
- id: 158aa2b8c3bc4373af134e54ef7e2ddf
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T19:00:49.087344+00:00
- updated_at: 2026-09-23T19:00:49.087344+00:00
- content: "There is a known trade-off: capping at 190 means creators with more videos lose daily snapshots for the excess, which is accepted but should be documented."

## entry
- id: 499589d0369147c492f5586da2aaf47c
- source: ai
- confidence: 0.9
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Placing normalization after decode but before merge ensures consistent per-file levels in the merged output; without it, dynamic range/levels vary per file and final results are inconsistent."

## entry
- id: 34bd14ea05234fd9b728542994ce57ec
- source: ai
- confidence: 0.8
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "The new tests use a flask stub; care must be taken that the stub does not leak into sys.modules (failure mode remains `No module named 'flask'`)."

## entry
- id: 84ca1a2450914d7799d3dc03c43d3577
- source: ai
- confidence: 0.8
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Refactoring a CLI script into a library function requires separating error semantics: in-processing errors become exceptions, while CLI front-end (main) retains exit codes/messages."

## entry
- id: 265a73859b19411da88806d63911bda8
- source: ai
- confidence: 1.0
- created_at: 2026-10-04T05:51:01.878813+00:00
- updated_at: 2026-10-04T05:51:01.878813+00:00
- content: "When observations carry no engineering signal, do not fabricate architecture, conventions, or bugs; emit empty category arrays rather than inventing plausible project details."

## entry
- id: aecb4bb8aa5943a7bf235bbcddbd48ef
- source: ai
- confidence: 0.9
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Because each method tab exposes its state as page-global variables, settings export/import can be implemented entirely client-side, avoiding any backend change."

## entry
- id: 7810871a848a4033b9ab29a581bda3ae
- source: ai
- confidence: 0.9
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Any new import format must be matched and short-circuited before the legacy folders branch, otherwise it would be POSTed to import_analyze."

## entry
- id: 6e5eb607d82b4f8c92d8d79af05d066f
- source: ai
- confidence: 0.85
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "A Node stub-DOM harness replaying the rendered page JS was effective for verifying client-side save/load round-trips without a browser."

## entry
- id: 1f995251c05f4d2d9564e9e6c32885b9
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Static source reading suggested the code was consistent; only executing the page (negative control on HEAD) revealed the Save/Load block was entirely absent — runtime harnesses are necessary to distinguish 'code wrong' from 'code never loaded'."

## entry
- id: 3fe93436195e4b8ab416ee7963424fab
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Inline script scoping is a real failure mode: typeof checks on const/let globals evaluated before the script runs return 'undefined', silently disabling new-format detection."

## entry
- id: a4c84f6ad3d041dc9e5d4106f2ca9e54
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Instrumenting with console.log of parsed JSON plus structured warn/error payloads (method, top-level keys, config keys) makes each failure class (bad type, unknown method, missing config, render failure) distinguishable in DevTools."
