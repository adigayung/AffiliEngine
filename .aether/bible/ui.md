# bible:ui
<!-- AETHER BIBLE (machine-readable). format=entry-v1. -->
<!-- Setiap entri dimulai dengan marker '## entry'. -->
<!-- Tambahkan knowledge lewat ProjectBrain/AETHER; jangan edit manual. -->

## entry
- id: 75177d0e9c1b494e8933428247b2e4f0
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "templates/creator/report.html: per-job checkbox class is `bulk-job-checkbox`; it now also renders for scheduled jobs and carries a `data-job-status` attribute."

## entry
- id: 4c14a2e0c81b48eab58960809cd39dd9
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "Bulk delete confirmation modal is `#modalConfirmBulkDelete` and contains a 'Hapus folder project video' option wrapped in `#bulk-delete-folder-wrapper`; the wrapper is hidden when only scheduled jobs are selected, replaced with a note that files are not deleted."

## entry
- id: 6d453e6d818b47fba4e75431d979a1b5
- source: ai
- confidence: 0.9
- created_at: 2026-09-22T06:27:09.897281+00:00
- updated_at: 2026-09-22T06:27:09.897281+00:00
- content: "'Remove Schedule' modal has a bullet `#remove-folder-bullet` ('Menghapus folder schedule…') which is hidden for scheduled jobs and replaced with a note that files are not deleted."

## entry
- id: 3353b5a1f4ef43cba3e17b70e93f1f91
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:10:32.423510+00:00
- updated_at: 2026-09-23T16:10:32.423510+00:00
- content: "\"View Harian — 45 Hari Terakhir\" section is at templates/video_analytics/index.html:383; chart canvas is #dailyViewsChart at :390, populated via daily_views_chart variable rendered at :1163."

## entry
- id: 4ec20d13ce744349a113a8dc92abd211
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:10:32.423510+00:00
- updated_at: 2026-09-23T16:10:32.423510+00:00
- content: "Report page listing UI is templates/creator/report.html, backed by get_creator_upload_schedule() (live aggregation from upload_jobs)."

## entry
- id: b512cbf8da1949cb956fac772732237a
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "templates/video_analytics/index.html: 'Perubahan hari ini' badge rendered at lines 170-175 immediately after 'Total Views'; chart section at :383, canvas #dailyViewsChart at :390, JS variable daily_views_chart at :1163. Template only consumes values; it is not the source of the computation."

## entry
- id: 9de9e71c41f941a4ba4ca0aeefa8b9df
- source: ai
- confidence: 0.85
- created_at: 2026-09-23T16:28:38.376583+00:00
- updated_at: 2026-09-23T16:28:38.376583+00:00
- content: "Summary card shows aggregate metrics for a creator: Total Video, Total Views, Avg, Median, Highest, Lowest, plus the 'Perubahan hari ini' growth badge."

## entry
- id: e7c45efe785247ba9c32ed07fd078262
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Video analytics screen (templates/video_analytics/index.html) shows summary 'Perubahan Hari Ini' and a daily views chart; invariant required: summary_today == daily_views_chart[today]."

## entry
- id: 426b00892ab741ad827a912ca8050c35
- source: ai
- confidence: 0.8
- created_at: 2026-09-23T16:35:15.560647+00:00
- updated_at: 2026-09-23T16:35:15.560647+00:00
- content: "Per-video table retains field views_growth (last-snapshot growth) unchanged; new fields views_growth_today and snapshot_is_today added per video."

## entry
- id: 783cb3025e3e4fb8b3de39db24e4d885
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T17:03:00.979606+00:00
- updated_at: 2026-09-23T17:03:00.979606+00:00
- content: "The `POST /creator/{creator_id}/video_analytics/update` endpoint returns JSON with fields: `fetched`, `filtered`, `processed`, `processed_success`, `processed_failed`, `snapshots_written`, `skipped_no_id`, `failures`."

## entry
- id: 2475f97b00a44e58b9080652297f02e2
- source: ai
- confidence: 0.95
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "UI trigger for video analytics scan: POST /creator/<id>/video_analytics/update from templates/video_analytics/index.html:1227."

## entry
- id: e1fc8c1427d24b4199f016f912f86c5b
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "UI trigger for video performance scan: POST /creator/<id>/video_performance/scan from video performance page."

## entry
- id: afda23252c694a6383a3e6384c4a0461
- source: ai
- confidence: 0.9
- created_at: 2026-09-23T19:00:49.086344+00:00
- updated_at: 2026-09-23T19:00:49.086344+00:00
- content: "Video analytics page includes chart 'View Harian — 45 Hari Terakhir' (45-day window) and summary 'Perubahan Hari Ini' which must remain unchanged."

## entry
- id: 3a3ad77320c14b26b7150db830046d3f
- source: ai
- confidence: 0.95
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "/video_pipeline/ page option order (top to bottom): Preserve Audio -> Tambahkan Music (default ON) -> Edit Audio dB. The new 'Normalize Audio' checkbox (id=\"normalizeAudio\", name=\"normalize_audio\") is inserted between 'Tambahkan Music' and 'Edit Audio dB'."

## entry
- id: 202aecea87404cf5a3bb832684c8a534
- source: ai
- confidence: 0.95
- created_at: 2026-10-04T05:42:01.263460+00:00
- updated_at: 2026-10-04T05:42:01.263460+00:00
- content: "Normalize Audio checkbox defaults to checked (ON) via HTML `checked` attribute, and is submitted as form.append(\"normalize_audio\", checked ? \"1\" : \"0\"), disabled/enabled together with others in setButtonState()."
