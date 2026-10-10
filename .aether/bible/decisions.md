# bible:decisions
<!-- AETHER BIBLE (machine-readable). format=entry-v1. -->
<!-- Setiap entri dimulai dengan marker '## entry'. -->
<!-- Tambahkan knowledge lewat ProjectBrain/AETHER; jangan edit manual. -->

## entry
- id: 800d5508befa4813a6229d153f9d803a
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Reused the existing `bulk_delete_upload_jobs()` endpoint (POST /creator/<id>/report/bulk_delete) to handle both pending and scheduled jobs instead of creating a new endpoint."

## entry
- id: 2dbe8c945dac400483ab13fc1dd15e08
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Scheduled delete logic reuses `_compute_display_status` so deletion conditions stay consistent with report page display."

## entry
- id: 7f8896a31e5e48c0b2a46c7710c35839
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "`delete_folders` parameter applies only to pending jobs; scheduled jobs never trigger folder/file deletion even when delete_folders=true."

## entry
- id: 3a1d92911fef44a28d503c3baa672078
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "`_bulk_delete_pending_jobs()` was left untouched to preserve pending delete behavior (no regressions)."

## entry
- id: 20c21b7f510e4d46838add6c2b7b9a66
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.423510+00:00
- updated_at: 2026-09-23T16:10:32.423510+00:00
- content: "Daily historical view metrics are stored as immutable per-day snapshots (keyed by video_id + snapshot date) in tiktok_video_stats; the chart reads from these snapshots rather than live job/product state."

## entry
- id: 24f52aad19a542aebae1751cf0292440
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.423510+00:00
- updated_at: 2026-09-23T16:10:32.423510+00:00
- content: "Snapshot upsert only overwrites today's row (WHERE video_id=%s AND DATE(snapshot_time)=%s); past days are never rewritten, so past-day values are effectively frozen."

## entry
- id: 1e5f4d41cc1a45f38a087f8538116cfb
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.423510+00:00
- updated_at: 2026-09-23T16:10:32.423510+00:00
- content: "Product/job deletion deletes only upload_jobs rows (and filesystem folders); it does not touch tiktok_videos or tiktok_video_stats, so analytics history is not retroactively affected."

## entry
- id: 7c981f59ef4049f0b93bd645d6dd570f
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.424510+00:00
- updated_at: 2026-09-23T16:10:32.424510+00:00
- content: "Reported retroactive-change issue on video_analytics chart was judged NOT a bug; no code changes were made (Step 1.d stop)."

## entry
- id: 21c1a5daaab74bd6ba99e702aca01ebf
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Decision on source of truth: the chart value (total_delta_map[today]) is the correct 'view hari ini', because it restricts to snapshots dated CURDATE(), clamps deltas with max(0, Δ), and is immutable/per-date (non-retroactive). The summary value is deemed misleading and should either be recomputed from today-only deltas or be relabeled."

## entry
- id: 1c1bb8de9a444c12af2af330d422edb3
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Proposed (NOT yet implemented) sync plan: (1) routers/creator/video_analytics.py:79 compute total_views_growth from today-only deltas or reuse the chart's last point; (2) _read_analytics (~316/394) add snapshot_is_today / as_of_date flags and separate views_growth_today from views_growth_last_capture; (3) template :170-175 clarify labels/tooltips; (4) consider raising routers/creator/video_analytics.py:40 max_videos = 90 to reduce stale-video gap."

## entry
- id: 6cba68b962a94fcb85e894f3302d7a1c
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Summary 'Perubahan Hari Ini' now sums views_growth_today per video, counted only when the video's latest snapshot date equals today."

## entry
- id: 870f011f5615426cacacfe6c11436d62
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "views_growth_today = max(0, curr.views - prev.views) if snapshot_is_today and prev exists, else 0."

## entry
- id: f55a6bda47ba4e50b134dcb589da4d34
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Kept views_growth field (raw last-snapshot growth) for per-video table display; chart untouched."

## entry
- id: df6027b653d540e2b40e2427d416ce03
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Chose to leave max_videos = 90 unchanged and the 45-day chart historical output unchanged."

## entry
- id: 822e2c97d8be4bd5b9d647cfc43a7c48
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Changed `max_videos` to `0` (unlimited) in both the router (`routers/creator/video_analytics.py`) and the performance scanner (`includes/video_performance/scanner.py`)."

## entry
- id: e44a26a72d2843a38d3b849b948e9981
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Replaced magic sentinel `999999` with `UNLIMITED_VIDEOS = 0` and a `self.unlimited` flag in `TikTokScraper`."

## entry
- id: 4f0b90e9bb7a4b87a94f8a52a54bb5f6
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Modified `_scroll_until_done` in scraper to early-return only when an explicit cap is set; otherwise scroll until `STALL_LIMIT` (natural stop)."

## entry
- id: fb35d59788024c90a4b1f1abe973a7b1
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Changed progress calculation in scraper to handle unlimited mode and avoid `ZeroDivisionError`."

## entry
- id: 3a9977c3eed44db1a2ed2ebb99cd2ce0
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Added failure counters and coverage metrics to `VideoAnalyticsService.update_creator_analytics`; failures are now logged as `FAILED video <id>: <error>` and returned in the endpoint response."

## entry
- id: b623805f68aa4c8a8037dfd06eaa16d7
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "Created `tests/test_video_analytics_scan_coverage.py` with 16 tests."

## entry
- id: 33a8abe61edd4796b9a2b7d11b40d819
- source: consultant
- confidence: 0.8
- created_at: 2026-09-23T18:00:56.793321+00:00
- updated_at: 2026-09-23T18:00:56.793321+00:00
- content: "PROPOSED (belum diimplementasikan, belum diverifikasi di source — Project Map masih MISSING). Task Proposal: batasi scan video_analytics dengan MAX_SCROLLS (default 6, boleh 6-8) di dalam loop _scroll_until_done() DAN hard cap MAX_VIDEOS_PER_CREATOR = 190 video UNIK (dedup-aware), berhenti segera saat salah satu tercapai; hapus perilaku max_videos=0 (UNLIMITED_VIDEOS) sebagai default pada jalur router video_analytics + VideoPerformanceScanner. Batas utama di level scraper/scroll (pengendali browser), ditambah guard defensif berlog sebelum pemrosesan/penulisan snapshot (bukan slice senyap). Ini MEMBALIK keputusan lama ('0 = unlimited', 'jangan hardcoded cap') untuk jalur ini sehingga konvensi lama harus direvisi. Trade-off diakui: creator dengan >190 video (mis. creator_id=2 punya 195) akan kehilangan snapshot harian sebagian video -> potensi gap 'perubahan hari ini' vs chart 45 hari muncul kembali sebagai known_gap, bukan bug baru. Tidak boleh mengubah tiktok_videos/tiktok_video_stats (tanpa DELETE/TRUNCATE), kontrak endpoint POST /creator/{creator_id}/video_analytics/update, format log Scan summary, atau window chart 45 hari. Fase 0 read-only wajib (baca scraper.py: konstruktor/_scroll_until_done/STALL_LIMIT/_merge & dedup; router ~40; scanner ~58 & 82; rantai pemanggilan; modul konstanta bersama) sebelum menulis kode karena nomor baris di Bible masih indikatif."

## entry
- id: 0175e9bbb421421ea1354f574de55880
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "Previous caps existed (router max_videos=90, scanner max(20, scroll_count*10), scraper min(500, max_videos*2+5)) but were removed in favor of max_videos=0 (unlimited). This decision caused the current performance regression and is being reversed."

## entry
- id: 1dec7a0f72374e44869d1d25fed9a7a2
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "Proposed decision: enforce hard cap of MAX_VIDEOS_PER_CREATOR=190 unique videos per creator per scan, and MAX_SCROLLS=6 (range 6-8) at scraper level, with defensive guards before DB insert."

## entry
- id: 67bcf8de203e4aa6b79225060c04dfbb
- source: ai
- confidence: 0.9
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Extracted CLI logic in audio_normalize.py into a programmatic function `normalize_video_file(input_path, output_path=None, ..., log_callback=None)` returning the output path or None (never sys.exit)."

## entry
- id: f44fd01d9ee046408e4fdb091d837f1c
- source: ai
- confidence: 0.9
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Added a `_normalize_audio_step()` helper in processor.py; normalization output becomes the input to the next pipeline step (edit audio dB / add sound)."

## entry
- id: 343ecbb0bed4401db81c14c9c4015d36
- source: ai
- confidence: 0.9
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Normalization is applied per individual MP4 file after decode and before merge, placing it before edit-audio-dB and add-sound steps."

## entry
- id: 9cb441b8dad74d0697fa4fd9ceb4cdc1
- source: ai
- confidence: 0.85
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "A `log_callback` (`_emit`) is threaded through normalize functions so messages surface in the pipeline UI console; the ffmpeg filter chain itself was left unchanged."

## entry
- id: 386c979afc404671ba2f11aa67c364ba
- source: ai
- confidence: 0.85
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Default values are inconsistent across layers: PipelineRunner.start() defaults normalize_audio=True, while processor create_video()/_process_single_folder() default normalize_audio=False; router start() defaults to True when form field missing/empty."

## entry
- id: ecc5f47c97034bcf8e48139fa88a8d0c
- source: ai
- confidence: 0.95
- created_at: 2026-10-04T05:51:01.878813+00:00
- updated_at: 2026-10-04T05:51:01.878813+00:00
- content: "Task explicitly instructed: do not write any code, do not read any files, respond only with 'hallo'. Compliance was the goal over any engineering outcome."

## entry
- id: 0fa4ec291c534b519f13b9869367e94c
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "New settings JSON schema: {type:\"upload_schedule_settings\", version:1, distribution_method:\"existing\"|\"balanced\", method:\"interval\"|\"fixed\"|\"weekly\"|\"pattern\", config:{...}}. Per-method config: interval {start_time, interval_hour}; fixed {upload_times:[...]}; weekly {weekly_schedule:{Monday..Sunday:[...]}}; pattern {stages:[{duration,unit:\"days\"|\"weeks\"|\"months\"|\"until_finish\", strategy:\"interval\"|\"fixed\"|\"weekly\", config:{interval_hour/interval_minute|times[]|schedule{}}}]}."

## entry
- id: 7bdf633e947f48c6a02e24aec9810f31
- source: ai
- confidence: 0.9
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Save exports only the currently filled method's config (no merging across methods), plus distribution_method and the active method."

## entry
- id: 0211447f3ed44f789604824b5666b1c2
- source: ai
- confidence: 0.95
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Settings download is done purely client-side via JSON.stringify -> Blob -> temporary <a download> (filename upload_schedule_settings_<method>.json) -> revokeObjectURL; no network request."

## entry
- id: 2e8e5361c2e94e3aa370ead213153af0
- source: ai
- confidence: 0.9
- created_at: 2026-10-10T16:09:44.054903+00:00
- updated_at: 2026-10-10T16:09:44.054903+00:00
- content: "Applied changes touch 6 templates only: prepare_jadwal.html (shared helpers), interval.html, fixed_time.html, weekly.html, pattern.html, import_schedule.html. Routers/product_list/index.py unchanged."

## entry
- id: 3a6cd9a9c4a34ead9d6d6cf7c8023975
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "Split analyzeImportFile() into JSON.parse (own try/catch) plus a new applyNewScheduleSettings() that performs dynamic lookup and invocation of the handler; new-format detection no longer depends on the global function existing at handler-registration time."

## entry
- id: 5777e6fed50a4648a3569fc48f3c0307
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "showTabForMethod() gained a manual fallback (activateNavLinkManually) toggling 'active'/'show' classes when bootstrap or bootstrap.Tab is unavailable or .show() throws."

## entry
- id: b8f617d92cea4068a2730d00d9ad6f8c
- source: ai
- confidence: 1.0
- created_at: 2026-10-10T16:46:34.272274+00:00
- updated_at: 2026-10-10T16:46:34.272274+00:00
- content: "applyFixedSettings normalizes both upload_times and uploadTimes, coerces values to 'HH:MM' strings, then verifies the DOM render and retries renderUploadTimes() once with console.error on failure."
