"""
Matching Engine - Menghubungkan video dengan upload_jobs.

Tugas:
1. Membaca upload_jobs yang belum memiliki video_id
2. Membaca tiktok_videos yang belum memiliki upload_job_id
3. Pre-filter berdasarkan waktu upload
4. Normalisasi caption
5. Fuzzy matching dengan SequenceMatcher
6. Update relasi dua arah jika match

TIDAK melakukan scan atau akses database langsung.
"""

import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from includes.mysql import (
    get_unmatched_videos_for_matching,
    get_upload_jobs_for_matching,
    update_video_matching,
    update_upload_job_video_id,
)


class MatchingEngine:
    """
    Engine untuk mencocokkan video TikTok dengan upload_jobs.
    """

    def __init__(self, time_window_minutes: int = 120, score_threshold: float = 0.8):
        """
        Args:
            time_window_minutes: Toleransi selisih waktu upload (menit)
            score_threshold: Threshold minimal match score (0.0 - 1.0)
        """
        self.time_window_minutes = time_window_minutes
        self.score_threshold = score_threshold

    def normalize_caption(self, caption: str) -> str:
        """
        Normalisasi caption untuk matching.

        Langkah:
        - lowercase
        - trim
        - hapus hashtag (#xxx)
        - hapus emoji
        - hapus multiple spaces
        """
        if not caption:
            return ""

        text = caption.lower().strip()

        # Hapus hashtag
        text = re.sub(r"#[a-zA-Z0-9_]+", "", text)

        # Hapus URL
        text = re.sub(r"https?://\S+", "", text)

        # Hapus emoji (range Unicode)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Symbols & pictographs
            "\U0001F680-\U0001F6FF"  # Transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # Flags
            "\u2702-\u27B0"          # Dingbats
            "\u24C2-\U0001F251"      # Enclosed characters
            "]+",
            flags=re.UNICODE,
        )
        text = emoji_pattern.sub("", text)

        # Hapus multiple spaces
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _parse_datetime(self, dt_val):
        """Parse datetime value to datetime object."""
        if dt_val is None:
            return None
        if isinstance(dt_val, (datetime,)):
            return dt_val
        if isinstance(dt_val, str):
            try:
                return datetime.strptime(dt_val, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    return datetime.strptime(dt_val, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    return None
        return None

    def is_within_time_window(self, video_upload_time, job_schedule_datetime) -> bool:
        """
        Cek apakah video_upload_time dan job_schedule_datetime
        berada dalam time_window_minutes yang sama.

        Returns:
            bool: True jika selisih <= time_window_minutes
        """
        vt = self._parse_datetime(video_upload_time)
        jt = self._parse_datetime(job_schedule_datetime)

        if vt is None or jt is None:
            return False

        diff = abs((vt - jt).total_seconds()) / 60
        return diff <= self.time_window_minutes

    def calculate_score(
        self,
        video_upload_time,
        job_schedule_datetime,
        video_caption: str,
        job_caption: str,
    ) -> float:
        """
        Hitung composite score antara video dan upload_job.

        Parameter:
        1. Creator sama (dipastikan oleh caller)
        2. Selisih waktu upload (time proximity)
        3. Caption similarity (SequenceMatcher)

        Composite Formula:
        - time_score: 0.0 - 0.4 (semakin dekat waktunya, semakin tinggi)
        - caption_score: 0.0 - 0.6 (semakin mirip caption, semakin tinggi)
        - total = time_score + caption_score

        Returns:
            float: Score 0.0 - 1.0
        """
        # --- Time Score (0.0 - 0.4) ---
        vt = self._parse_datetime(video_upload_time)
        jt = self._parse_datetime(job_schedule_datetime)

        time_score = 0.0
        if vt is not None and jt is not None:
            diff_minutes = abs((vt - jt).total_seconds()) / 60
            if diff_minutes <= self.time_window_minutes:
                # Linear: 0 menit -> 0.4, time_window -> 0.0
                time_score = max(0.0, 0.4 * (1 - diff_minutes / self.time_window_minutes))

        # --- Caption Score (0.0 - 0.6) ---
        norm_video = self.normalize_caption(video_caption)
        norm_job = ""

        # job_caption bisa dari folder name atau caption dari schedule
        if job_caption:
            norm_job = self.normalize_caption(job_caption)

        caption_score = 0.0
        if norm_video and norm_job:
            caption_score = SequenceMatcher(None, norm_video, norm_job).ratio() * 0.6
        elif not norm_video and not norm_job:
            # Keduanya kosong -> time_score determines everything
            caption_score = 0.0
        # Jika salah satu kosong, caption_score tetap 0

        total = time_score + caption_score
        return min(total, 1.0)

    def match(self, creator_id: int) -> list[dict]:
        """
        Jalankan matching untuk semua video unmatched milik creator.

        Flow:
        1. Ambil semua video yang belum punya upload_job_id
        2. Ambil semua upload_jobs yang belum punya video_id
        3. Untuk setiap video, cari job terbaik berdasarkan:
           a. Time window pre-filter
           b. Composite score (time + caption)
        4. Jika score >= threshold, update relasi dua arah

        Args:
            creator_id: ID creator

        Returns:
            list[dict]: Hasil matching dengan keys:
                - video_id: str
                - upload_job_id: int
                - match_score: float
                - match_method: str ("auto")
        """
        results = []

        # 1. Ambil unmatched videos
        videos = get_unmatched_videos_for_matching(creator_id)
        if not videos:
            return results

        # 2. Ambil unmatched upload_jobs
        jobs = get_upload_jobs_for_matching(creator_id)
        if not jobs:
            return results

        # 3. Untuk setiap video, cari job terbaik
        for video in videos:
            video_id = video["video_id"]
            video_time = video.get("upload_time")
            video_caption = video.get("caption", "")

            best_job = None
            best_score = 0.0

            for job in jobs:
                job_id = job["id"]
                job_time = job.get("schedule_datetime")
                job_caption = job.get("folder", "")  # folder name sebagai caption fallback

                # Pre-filter: time window
                if not self.is_within_time_window(video_time, job_time):
                    continue

                # Hitung composite score
                score = self.calculate_score(
                    video_time, job_time,
                    video_caption, job_caption,
                )

                if score > best_score:
                    best_score = score
                    best_job = job

            # 4. Jika score memenuhi threshold, update
            if best_job is not None and best_score >= self.score_threshold:
                upload_job_id = best_job["id"]

                # Update tiktok_videos (relasi video -> upload_job)
                update_video_matching(
                    video_id=video_id,
                    upload_job_id=upload_job_id,
                    match_score=best_score,
                    match_method="auto",
                )

                # Update upload_jobs (relasi upload_job -> video)
                update_upload_job_video_id(
                    job_id=upload_job_id,
                    video_id=video_id,
                )

                results.append({
                    "video_id": video_id,
                    "upload_job_id": upload_job_id,
                    "match_score": best_score,
                    "match_method": "auto",
                })

                # Hapus job yang sudah matched dari daftar
                jobs = [j for j in jobs if j["id"] != upload_job_id]

                if not jobs:
                    break

        return results
