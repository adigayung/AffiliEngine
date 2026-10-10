# bible:conventions
<!-- AETHER BIBLE (machine-readable). format=entry-v1. -->
<!-- Setiap entri dimulai dengan marker '## entry'. -->
<!-- Tambahkan knowledge lewat ProjectBrain/AETHER; jangan edit manual. -->

## entry
- id: 3e06821787f046609dfbfe9fd2824c1d
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Reuse existing patterns/endpoints rather than adding new tools or endpoints when a pattern (e.g. the pending delete flow) can be reused."

## entry
- id: bad2d25d6dc4420fa40f3b499ca52dcb
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "New delete behavior must follow the existing 'pending' delete UI/backend pattern for consistency, and must not change pending delete behavior."

## entry
- id: 631320ca28614b02ae8ce0fe32027782
- source: ai
- confidence: 0.85
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Verify status definitions in source before implementing status-dependent behavior; do not assume status semantics."

## entry
- id: bfa7bfd83b9743d88c00a36556c86edd
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:10:32.423510+00:00
- updated_at: 2026-09-23T16:10:32.423510+00:00
- content: "Follow project structure: routes in routers/, domain logic in includes/, Jinja in templates/, tests in tests/."

## entry
- id: 96bb6c0e59624ee7a73403c6b7609705
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:10:32.423510+00:00
- updated_at: 2026-09-23T16:10:32.423510+00:00
- content: "Do not change or remove the existing delete endpoint contract POST /creator/<id>/report/bulk_delete."

## entry
- id: 22e474b0d1a144eda10b7ebb14b3cc33
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:10:32.423510+00:00
- updated_at: 2026-09-23T16:10:32.423510+00:00
- content: "Schema changes must go through migrations, never manual DB edits."

## entry
- id: f419efd94ba04cb490447efce1bcc9fb
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:10:32.423510+00:00
- updated_at: 2026-09-23T16:10:32.423510+00:00
- content: "Do not guess file paths or function names; verify by reading source (Investigate mode) before editing."

## entry
- id: cbcf82fcdae34e048405310efdb216ed
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:10:32.423510+00:00
- updated_at: 2026-09-23T16:10:32.423510+00:00
- content: "Verify first (read-only) and STOP without writing code if the reported issue turns out to be by-design/correct behavior."

## entry
- id: a204b65e8d8640d18ad3383096065ac1
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:10:32.423510+00:00
- updated_at: 2026-09-23T16:10:32.423510+00:00
- content: "Validation gate: py_compile must pass and Jinja templates must parse; relevant tests must pass (or at minimum py_compile)."

## entry
- id: 7476eb86b06e4308b3dab216495ca227
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Investigation tasks are READ ONLY: do not modify source or production DB, do not commit/push. Fixes are proposed only after root cause is confirmed by code + query evidence."

## entry
- id: 48c91b359efc4c61a1bf775ff6ea5d9a
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Analytics tables (tiktok_videos, tiktok_video_stats) are treated as append/immutable per-day snapshots; only today's row is overwritten. Never DELETE/TRUNCATE them."

## entry
- id: 512bbfc327d841118a94daa3ae55f4cf
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Follow repository layout conventions: HTTP handlers in routers/, domain logic in includes/, Jinja views in templates/, tests in tests/ (e.g. tests/test_creator_report_delete.py is the pattern for fake-DB tests)."

## entry
- id: a3370488576a4a83ad436c48c91a03fc
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Check actual implementation before changing code; fix only the path needed, avoid large refactors."

## entry
- id: 4606ee3b88ce4259a0777c09f884f8a6
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Do not change or delete existing snapshot history or old analytics data in tiktok_video_stats."

## entry
- id: ae1f7a7bda9e4d7d8123731405c322c2
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Do not change chart algorithm unless required to preserve the summary==chart sync invariant."

## entry
- id: 22dbb590a1394aca888cc06081c054b3
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Do not change max_videos capture scope in sync-fix tasks; that is a separate design/performance decision."

## entry
- id: 548587a12e7b421cb2c0f7933dfef6bf
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Preserve semantics of other metrics (Total Views, Avg Views, Median Views, Highest Views, Lowest Views) unless proven impacted by the same bug."

## entry
- id: b23e903529cc49648b48b42013030922
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Negative deltas follow existing chart contract: max(0, delta)."

## entry
- id: 44712f311274470f820f8a0abeae1571
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Do not use hardcoded video count caps (e.g., 90, 195, 200, 1000). The true limit is the number of videos successfully fetched from the source."

## entry
- id: 57281271d4d04a8dab2d381cf329b777
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "When a cap is needed, use `0` to mean unlimited (`UNLIMITED_VIDEOS = 0`)."

## entry
- id: 991d6a43e57a49eabf99991cd257e45e
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Slicing video lists should be opt-in: only apply `self.videos[:self.max_videos]` when `max_videos > 0`."

## entry
- id: 2f7142e10e0b4b99a46a2860ef052166
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Do not silently drop processing failures; log each failure and include failure counts in the scan summary."

## entry
- id: a6c6791502554d828a4843916581250a
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Required scan log format: `Scan summary creator {id} | Videos fetched: X | After filtering: X | Videos to process: X | Processed success: X | Processed failed: X | Snapshots written: X`."

## entry
- id: 6cf18f83def64965873fafc41f94a626
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Scope constraints: do not change `tiktok_video_stats`, snapshot history, 45-day chart window, analytics architecture, or endpoint contracts. Avoid DELETE/TRUNCATE and fake/duplicate data."

## entry
- id: 0a6aa7ae55af47fc8bcb7a403a4185ba
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Use regression tests to verify coverage: fetched N → processed N for N=195, 220, 87; ensure no `[:90]` or `[:100]` slicing."

## entry
- id: c817354e79664cd48f51c21b66517b74
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "Log format for scan summary must be preserved: 'Scan summary creator {id} | Videos fetched: X | After filtering: X | Videos to process: X | Processed success: X | Processed failed: X | Snapshots written: X'."

## entry
- id: 5c5fc273a6cc49778ebf8c87f4b20b7b
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "Database write behavior: use upsert (upsert_tiktok_video, upsert_video_daily_stats); no DELETE/TRUNCATE on tiktok_videos or tiktok_video_stats; daily stats upsert only overwrites today's row."

## entry
- id: cbe4bbf4ff3a48178a61ca4dc7c4d905
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "Endpoint contract for POST /creator/<creator_id>/video_analytics/update must not change (JSON field names and meanings: fetched, filtered, processed, snapshots_written)."

## entry
- id: f66f4641f13b41289e604e482cbdad72
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "Scraper uses max_videos=0 to mean unlimited (UNLIMITED_VIDEOS=0), with MAX_SCROLLS=500 and STALL_LIMIT=8. This convention is now considered harmful and should be replaced with hard cap 190 and max scrolls 6-8."

## entry
- id: afecbe3d6ea645288590614f2a91fab9
- source: ai
- confidence: 0.9
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Boolean form fields are parsed with the existing `_to_bool` pattern; missing/empty field should default to True."

## entry
- id: 0d8c3c11d14742dd9b48691759b69c5b
- source: ai
- confidence: 0.9
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Library modules must never call sys.exit() in processing paths; raise domain exceptions (e.g., AudioNormalizeError) and let the CLI main() translate them to exit 1 with stderr message."

## entry
- id: 45b1909714bd468bab9b597ec8668aa4
- source: ai
- confidence: 0.9
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Optional pipeline steps should be non-fatal: on failure or missing precondition, log [WARN]/[SKIP] and continue with the original file rather than failing the job."

## entry
- id: b2303679c91f4a83ae31781b09131402
- source: ai
- confidence: 0.85
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Intermediate files produced by a step must be registered in `temp_files` so they get cleaned up."

## entry
- id: 8dd86a31d8af4b01bc609c8d45363fe3
- source: ai
- confidence: 0.85
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Log each significant step clearly, e.g. `logger.info(\"Normalize audio: %s -> %s\", input, output)` and a header line `Normalize Audio: ...`."

## entry
- id: 6e7d2fd3ff064124abecf62ed1296315
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Do not rename existing shared state/functions: uploadTimes, weeklySchedule, stages, stageCounter, renderUploadTimes, renderWeekly, renderStages — only add new helpers alongside them."

## entry
- id: 898dd07eb9da439daa2776cf20d5078d
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Preserve existing per-method submit contracts (schedule_mode, distribution_method, etc.) and existing Next button behavior."

## entry
- id: 614037f3ed4f42358c1c63869eb529f1
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Legacy import format ('folders' array) must keep working 100% unchanged: after JSON.parse, the new-format check (jsonData.type === \"upload_schedule_settings\") must run BEFORE the folders check, and on match apply settings, show a success alert and return without calling import_analyze."

## entry
- id: 3e0f87e7de8043c49831f91977d0ef45
- source: ai
- confidence: 0.9
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "When applying loaded state, always re-render via existing render functions (renderUploadTimes(), renderWeekly(day) per day, renderStages()) to keep UI consistent."

## entry
- id: faf848c775414d2880b7f52b30bed6ef
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Change scope is limited to client-side template/JS in 6 files; no new endpoint, table, or DB, no router change."

## entry
- id: 649cb7c521a6400692f231fb333b7787
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Top-level const/let declarations in inline scripts do NOT attach to window; shared load helpers must be referenced explicitly as window.applyScheduleSettings and looked up dynamically at click runtime (not at parse time via typeof)."

## entry
- id: a45b59450edc47e6aa1450607c9ed4f5
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "No silent failures: every failure path must emit an informative alert plus console.error/console.warn naming the cause (unknown method, bad file type, load function unavailable, render failure)."

## entry
- id: 3f9e76777e38434ea36255f93529d8ac
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Apply functions must not throw on missing config (tolerate undefined data.config), must normalize input types (e.g. numeric times to 'HH:MM' strings), and should accept alternative key spellings (uploadTimes as alias of upload_times) for backward compatibility while writing only the canonical schema."

## entry
- id: 02488f6c16ae409c99674eebfb7b13ec
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Do not reorder tab script includes to fix load-timing issues; fix by deferring lookup until runtime click. Do not touch Upload Directory/Start Date, the legacy folders import flow, or the Next-button submit contract."

## entry
- id: a3ca41f867844cf5b0f087605e997faf
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Preserve existing state/global names: uploadTimes, weeklySchedule, stages, renderUploadTimes, renderWeekly, renderStages."

## entry
- id: 7f839f6ff58644bd8a3923d8834d29a9
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "When applying schedule settings, dispatch a synthetic 'change' event on the selected distribution_method radio so downstream state handlers actually run."
