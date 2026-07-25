-- ============================================================
-- MIGRATION: Arsitektur Baru Video Performance
-- Tanggal: Juli 2025
-- ============================================================
-- Perubahan:
-- 1. tiktok_videos tetap tanpa kolom statistik (hanya metadata)
-- 2. Menambahkan kolom likes/comments/shares ke tiktok_video_stats
-- ============================================================
-- CATATAN:
-- Tabel tiktok_video_stats sudah memiliki kolom:
--   id, video_id, snapshot_time (DATETIME), views,
--   created_at, updated_at
--
-- Tabel tiktok_videos sudah memiliki kolom:
--   id, video_id, creator_id, video_url, caption, upload_time,
--   first_detected, last_scan, upload_job_id, match_score,
--   match_method, matched_at
-- ============================================================
-- ============================================================
-- 1. ALTER TABLE tiktok_videos
-- ============================================================
-- tiktok_videos hanya menyimpan METADATA video.
-- Statistik (views, likes, comments, shares) disimpan di tiktok_video_stats.
-- Tidak perlu menambahkan kolom statistik ke tiktok_videos.
ALTER TABLE tiktok_videos
    ADD INDEX IF NOT EXISTS idx_creator_id (creator_id),
    ADD INDEX IF NOT EXISTS idx_upload_time (upload_time);

-- ============================================================
-- 2. ALTER TABLE tiktok_video_stats
-- ============================================================
-- Tambahkan kolom likes, comments, shares
ALTER TABLE tiktok_video_stats
    ADD COLUMN IF NOT EXISTS likes INT DEFAULT 0 AFTER views,
    ADD COLUMN IF NOT EXISTS comments INT DEFAULT 0 AFTER likes,
    ADD COLUMN IF NOT EXISTS shares INT DEFAULT 0 AFTER comments;

-- Tambahkan index untuk performa query
ALTER TABLE tiktok_video_stats
    ADD INDEX IF NOT EXISTS idx_video_id (video_id),
    ADD INDEX IF NOT EXISTS idx_snapshot_time (snapshot_time);

