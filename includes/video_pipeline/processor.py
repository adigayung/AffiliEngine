"""
processor.py — Orchestrates the entire video pipeline for a root folder.

Workflow:
  1. Scan root folder recursively for a.mp4 files.
  2. For each valid a.mp4 (with sound.json in same dir):
     a. decode_video(a.mp4) -> decode_output.mp4
     b. normalize audio per-file (opsional, default ON) -> output_normalized.mp4
     c. edit audio dB (opsional)
     d. add_sound(...) -> sound_output.mp4
     e. zoom_video(sound_output.mp4, 1.05) -> zoom_output.mp4
     f. upscale_video(zoom_output.mp4) -> upscale_output.mp4
     g. Move final output to job_dir/<name_from_schedule.json>
     h. Clean up temporary files (only pipeline-created files)
  3. Report progress via callback (for realtime logging)
"""

from pathlib import Path
from typing import Callable, Optional, List
import json
import logging
import shutil
import subprocess

from includes.video_pipeline.decode_video import decode_single_video
from includes.video_pipeline.add_sound import add_sound
from includes.video_pipeline.zoom_video import zoom_video
from includes.video_pipeline.upscale_video import upscale_video
from includes.video_pipeline.audio_normalize import normalize_video_file


logger = logging.getLogger(__name__)


# ================================================================
# Scanning
# ================================================================

def _scan_folders(root_path: str, add_music: bool = True) -> list[dict]:
    """Scan root folder recursively for valid video folders.

    A valid folder must contain:
      - aseets/a.mp4

    Jika add_music=True, folder juga wajib memiliki aseets/sound.json.

    Args:
        root_path: Path folder root yang akan discan.
        add_music: Jika True, sound.json wajib ada (music akan diproses).
            Jika False, sound.json tidak diperlukan.

    Returns:
        List of dicts with keys:
          - video_path: str — full path to a.mp4
          - sound_json_path: str — full path to sound.json ("" jika tidak ada)
          - asset_dir: str — directory containing a.mp4 & sound.json
          - job_dir: str — parent directory of asset_dir (folder jadwal)
    """
    root = Path(root_path)
    results: List[dict] = []

    print("Scanning folder...")

    for video_file in root.rglob("a.mp4"):
        asset_dir = video_file.parent
        sound_json = asset_dir / "sound.json"

        print(f"  Found video: {video_file.resolve()}")

        if add_music:
            print(f"  Looking for sound: {sound_json.resolve()}")

            if not sound_json.exists():
                print(f"  [FAIL] sound.json tidak ditemukan, skip")
                continue

            print(f"  [OK] sound.json ditemukan")
            sound_json_path = str(sound_json.resolve())
        else:
            print(f"  [SKIP] sound.json tidak diperlukan (add_music=false)")
            sound_json_path = ""

        results.append({
            "video_path": str(video_file.resolve()),
            "sound_json_path": sound_json_path,
            "asset_dir": str(asset_dir.resolve()),
            "job_dir": str(asset_dir.parent.resolve()),
        })

    print(f"  Total folder ditemukan: {len(results)}")
    return results


# ================================================================
# Schedule — read output filename
# ================================================================

def _load_schedule(job_dir: str) -> Optional[dict]:
    """Load schedule.json from job_dir.

    Args:
        job_dir: Path to the job folder (parent of aseets/).

    Returns:
        Parsed JSON dict, or None on failure.
    """
    schedule_path = Path(job_dir) / "schedule.json"

    if not schedule_path.exists():
        print(f"  [FAIL] schedule.json tidak ditemukan: {schedule_path}")
        return None

    print(f"  Schedule: {schedule_path.resolve()}")

    try:
        with open(schedule_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [FAIL] Gagal membaca schedule.json: {e}")
        return None


def _get_output_filename(schedule: dict) -> Optional[str]:
    """Extract output filename from schedule.json's files.video field.

    Args:
        schedule: Parsed schedule.json dict.

    Returns:
        Filename string or None if missing.
    """
    files_obj = schedule.get("files", {})
    video_name = files_obj.get("video")

    if not video_name:
        print(f"  [FAIL] files.video tidak ditemukan di schedule.json")
        return None

    return video_name


# ================================================================
# Music Rotation
# ================================================================

def _load_sound_json(sound_json_path: str) -> Optional[dict]:
    """Load sound.json. READ ONLY — never write back.

    Args:
        sound_json_path: Path to sound.json.

    Returns:
        Parsed JSON dict, or None on failure.
    """
    try:
        with open(sound_json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [ERROR] Gagal membaca sound.json: {e}")
        return None


def _get_music_for_index(music_list: list, index: int) -> Optional[str]:
    """Get music file path using round-robin rotation.

    Args:
        music_list: List of music file paths from sound.json.
        index: Zero-based index of the current folder in processing order.

    Returns:
        Path to the music file, or None if list is empty.
    """
    if not music_list:
        return None
    return music_list[index % len(music_list)]


# ================================================================
# Edit Audio dB — relative volume gain helper
# ================================================================

def _has_audio_stream(file_path: Path) -> bool:
    """Cek apakah file media memiliki stream audio.

    Args:
        file_path: Path ke file media.

    Returns:
        True jika ada stream audio, False jika tidak atau gagal baca.
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        str(file_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return False
        data = json.loads(result.stdout)
        return any(s.get("codec_type") == "audio" for s in data.get("streams", []))
    except Exception:
        return False


def _adjust_audio_db(
    input_video: Path,
    audio_db: float,
    log_callback: Optional[Callable] = None,
) -> Path:
    """Terapkan relative volume gain (dB) pada audio sebuah video.

    Hanya stream audio yang diganti (re-encode AAC), stream video di-copy
    (tidak re-encode). Gain diterapkan pada audio hasil decode/merge sehingga
    audio a.mp4 / b.mp4 tidak hilang pada tahap reverse/merge.

    Args:
        input_video: Path video input.
        audio_db: Gain relatif dalam dB (5, +5, -3, 0).
        log_callback: Optional log function.

    Returns:
        Path hasil gain jika berhasil, atau input_video jika:
          - audio_db == 0 (tanpa perubahan)
          - video tidak memiliki audio (skip, tidak gagal)
          - ffmpeg gagal / tidak ditemukan (lanjut tanpa perubahan)
    """
    def _log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)

    if audio_db == 0:
        return input_video

    if not _has_audio_stream(input_video):
        _log("  [SKIP] Video tanpa audio, lewati edit audio dB")
        return input_video

    output_path = input_video.with_stem(input_video.stem + "_db")
    db_str = f"{audio_db:g}"

    cmd = [
        "ffmpeg",
        "-i", str(input_video),
        "-af", f"volume={db_str}dB",
        "-c:v", "copy",
        "-c:a", "aac",
        "-y", str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=None)
    except FileNotFoundError:
        _log("  [WARN] ffmpeg tidak ditemukan, lewati edit audio dB")
        return input_video
    except Exception as e:
        _log(f"  [WARN] Gagal edit audio dB: {e}")
        return input_video

    if result.returncode != 0:
        _log("  [WARN] Edit audio dB gagal, lanjut tanpa perubahan")
        try:
            if output_path.exists():
                output_path.unlink()
        except Exception:
            pass
        return input_video

    if output_path.exists() and output_path.stat().st_size > 0:
        _log(f"  [OK] Audio dB diterapkan: {db_str} dB")
        return output_path

    _log("  [WARN] Edit audio dB: output tidak ditemukan")
    return input_video


# ================================================================
# Normalize Audio — per-file loudness/level normalization helper
# ================================================================

def _normalize_audio_step(
    input_video: Path,
    log_callback: Optional[Callable] = None,
) -> Optional[Path]:
    """Normalisasi audio satu file video (mp4) sebelum digabungkan.

    Memanggil wrapper library ``normalize_video_file()`` dari
    ``includes/video_pipeline/audio_normalize.py`` (bukan CLI) dan memakai
    output hasil normalisasi sebagai input langkah pipeline berikutnya.

    Args:
        input_video: Path video input (hasil decode/merge).
        log_callback: Optional log function.

    Returns:
        Path file hasil normalisasi bila berhasil, atau None bila dilewati
        (video tanpa audio) atau gagal — pipeline lanjut dengan file asli.
    """
    def _log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)

    if not _has_audio_stream(input_video):
        _log("  [SKIP] Video tanpa audio, lewati normalize audio")
        return None

    output_path = input_video.with_stem(input_video.stem + "_normalized")

    logger.info("Normalize audio: %s -> %s", input_video, output_path)

    normalized_path = normalize_video_file(
        str(input_video),
        str(output_path),
        log_callback=log_callback,
    )

    if not normalized_path:
        _log("  [WARN] Normalize audio gagal, lanjut tanpa normalisasi")
        return None

    normalized = Path(normalized_path)
    if not normalized.exists() or normalized.stat().st_size <= 0:
        _log("  [WARN] Normalize audio: output kosong, lanjut tanpa normalisasi")
        return None

    return normalized


# ================================================================
# Cleanup — only delete pipeline-created temp files
# ================================================================

def _cleanup_temp_files(temp_files: List[str], log_callback: Optional[Callable] = None):
    """Delete only the files that were created by the pipeline.

    Args:
        temp_files: List of absolute file paths to delete.
        log_callback: Optional log function.
    """
    def _log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)

    for file_path in temp_files:
        p = Path(file_path)
        if p.exists():
            try:
                p.unlink()
                _log(f"  Delete temp: {p.name}")
            except Exception as e:
                _log(f"  [WARN] Gagal hapus {p.name}: {e}")


# ================================================================
# Per-Folder Pipeline
# ================================================================

def _process_single_folder(
    folder_info: dict,
    music_index: int,
    log_callback: Optional[Callable] = None,
    preserve_audio: bool = False,
    add_music: bool = True,
    normalize_audio: bool = False,
    edit_audio_db: bool = False,
    audio_db: float = 0.0,
) -> bool:
    """Process a single folder through the video pipeline.

    Args:
        folder_info: Dict with video_path, sound_json_path, asset_dir, job_dir.
        music_index: Round-robin index for music selection.
        log_callback: Optional function to call for realtime log messages.
        preserve_audio: Jika True, audio asli video dipertahankan.
        add_music: Jika True, music dari sound.json ditambahkan.
        normalize_audio: Jika True, audio tiap file mp4 dinormalisasi
            (loudness/level) tepat setelah decode, sebelum edit audio dB
            dan sebelum add_sound.
        edit_audio_db: Jika True, relative audio gain (dB) diterapkan.
        audio_db: Besar gain relatif dalam dB (0 = tanpa perubahan).

    Returns:
        True if successful, False if any step failed.
    """
    video_path = folder_info["video_path"]
    sound_json_path = folder_info["sound_json_path"]
    asset_dir = Path(folder_info["asset_dir"])
    job_dir = Path(folder_info["job_dir"])
    folder_name = job_dir.name

    # List to track temp files created by this pipeline run
    temp_files: List[str] = []

    def _log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)

    _log(f"Folder: {folder_name}")

    # --- Load schedule.json untuk nama output ---
    schedule = _load_schedule(str(job_dir))
    if not schedule:
        _log("  [SKIP] schedule.json tidak valid")
        return False

    output_filename = _get_output_filename(schedule)
    if not output_filename:
        _log("  [SKIP] Nama output tidak ditemukan di schedule.json")
        return False

    final_output_path = job_dir / output_filename
    _log(f"  Output: {final_output_path.resolve()}")

    # --- Load sound.json & pilih music (hanya jika add_music=True) ---
    music_file = None
    if add_music:
        sound_data = _load_sound_json(sound_json_path)
        if not sound_data:
            _log("  [SKIP] Gagal membaca sound.json")
            return False

        music_list = sound_data.get("music_list", [])
        music_file = _get_music_for_index(music_list, music_index)
        if not music_file:
            _log("  [SKIP] music_list kosong")
            return False

        music_name = Path(music_file).name
        _log(f"  Music: {music_name}")
    else:
        _log("  Music: skip (add_music=false)")

    _log(f"  Video: a.mp4")

    # -- Step 1: Decode/Reverse --
    _log("  Decode/Reverse...")
    decode_output = decode_single_video(video_path, preserve_audio=preserve_audio)
    if not decode_output:
        _log("  [FAIL] Decode gagal")
        return False
    _log("  [OK]")

    decode_path = Path(decode_output)

    # a_2.mp4 dibuat oleh decode_single_video
    a2_path = asset_dir / "a_2.mp4"
    if a2_path.exists():
        temp_files.append(str(a2_path.resolve()))

    # decode_output (output.mp4) adalah hasil decode, ini temp
    temp_files.append(str(decode_path.resolve()))

    # -- Step 1b: Normalize Audio (opsional, default ON di UI) --
    # Dijalankan per-file mp4 SEBELUM langkah berikutnya (edit audio dB /
    # add sound), sehingga level/dynamic range tiap file konsisten sebelum
    # digabungkan.
    if normalize_audio:
        _log("  Normalize Audio...")
        normalized_path = _normalize_audio_step(decode_path, log_callback)
        if normalized_path is not None:
            temp_files.append(str(normalized_path.resolve()))
            decode_path = normalized_path
            _log(f"  [OK] Normalize audio: {decode_path.name}")
    else:
        _log("  Normalize Audio: skip")

    # -- Step 1c: Edit Audio dB (opsional, hanya aktif jika checkbox ON) --
    if edit_audio_db and audio_db != 0:
        _log(f"  Edit Audio dB: {audio_db:g} dB")
        adjusted_path = _adjust_audio_db(decode_path, audio_db, log_callback)
        if adjusted_path != decode_path:
            temp_files.append(str(adjusted_path.resolve()))
            decode_path = adjusted_path
    else:
        _log("  Edit Audio dB: skip")

    # -- Step 2: Add Sound (hanya jika add_music=True) --
    if add_music:
        _log("  Add Sound...")
        sound_output = add_sound(
            str(decode_path),
            music_file,
            preserve_audio=preserve_audio,
        )
        if not sound_output:
            _log("  [FAIL] Add Sound gagal")
            return False
        _log("  [OK]")

        sound_path = Path(sound_output)
        # sound_output adalah temp
        temp_files.append(str(sound_path.resolve()))
        # Input untuk step selanjutnya
        current_input = sound_path
    else:
        _log("  Add Sound: skip (add_music=false)")
        # Gunakan hasil decode langsung
        # (audio asli jika preserve_audio=true, tanpa audio jika false)
        current_input = decode_path

    # -- Step 3: Zoom 105% (menghilangkan watermark di pinggir) --
    _log("  Zoom 105%...")
    try:
        zoom_output = zoom_video(str(current_input), scale=1.05)
    except Exception as e:
        _log(f"  [FAIL] Zoom gagal: {e}")
        return False
    _log("  [OK]")

    zoom_path = Path(zoom_output)
    # zoom_output adalah temp
    temp_files.append(str(zoom_path.resolve()))

    # -- Step 4: Upscale --
    _log("  Upscale...")
    upscale_output = upscale_video(str(zoom_path))
    if not upscale_output:
        _log("  [FAIL] Upscale gagal")
        return False
    _log("  [OK]")

    upscale_path = Path(upscale_output)
    # upscale_output adalah temp
    temp_files.append(str(upscale_path.resolve()))

    # -- Move final output ke job_dir dengan nama dari schedule.json --
    try:
        if final_output_path.exists():
            final_output_path.unlink()
        shutil.move(str(upscale_path), str(final_output_path))
        # Hapus dari temp_files karena sudah dipindahkan & bukan temp lagi
        temp_files.remove(str(upscale_path.resolve()))
    except Exception as e:
        _log(f"  [FAIL] Gagal memindahkan output ke {final_output_path}: {e}")
        return False

    # -- Cleanup temporary files --
    _log("  Cleanup...")
    _cleanup_temp_files(temp_files, log_callback)
    _log("  [OK]")

    _log(f"  Output: {final_output_path.resolve()}")
    return True


# ================================================================
# Public API
# ================================================================

def create_video(
    root_path: str,
    log_callback: Optional[Callable] = None,
    preserve_audio: bool = False,
    add_music: bool = True,
    normalize_audio: bool = False,
    edit_audio_db: bool = False,
    audio_db: float = 0.0,
) -> dict:
    """Main entry point: process all videos in a root folder.

    Scans recursively for valid folders, runs the full pipeline on each,
    and reports results.

    Args:
        root_path: Absolute path to the root folder containing video projects.
        log_callback: Optional callable(text: str) for realtime log updates.
        preserve_audio: Jika True, audio asli video dipertahankan (default False).
        add_music: Jika True, music dari sound.json ditambahkan (default True).
        normalize_audio: Jika True, audio setiap file mp4 dinormalisasi
            (loudness/level) sesudah decode dan sebelum edit audio dB /
            add sound, supaya level tiap file konsisten sebelum digabungkan.
        edit_audio_db: Jika True, relative audio gain (dB) diterapkan pada audio video.
        audio_db: Besar gain relatif dalam dB (5, -3, 0). Diabaikan saat edit_audio_db=False.

    Returns:
        Dict with:
          - success: bool (True if at least one folder succeeded)
          - total: int
          - succeeded: int
          - failed: int
          - results: list of per-folder results
    """
    def _log(msg: str):
        if log_callback:
            log_callback(msg)

    _log("=" * 50)
    _log("Video Pipeline Started")
    _log("=" * 50)
    _log(f"Root: {root_path}")
    _log(f"Preserve Audio: {preserve_audio}")
    _log(f"Add Music: {add_music}")
    _log(f"Normalize Audio: {normalize_audio}")
    _log(f"Edit Audio DB: {edit_audio_db}")
    _log(f"Audio DB: {audio_db:g} dB")

    # Scan
    folders = _scan_folders(str(root_path), add_music=add_music)

    if not folders:
        _log("Tidak ada folder valid ditemukan.")
        _log("=" * 50)
        return {
            "success": False,
            "total": 0,
            "succeeded": 0,
            "failed": 0,
            "results": [],
        }

    # Process each folder
    succeeded = 0
    failed = 0
    results = []

    for idx, folder_info in enumerate(folders):
        _log("-" * 50)
        try:
            ok = _process_single_folder(
                folder_info,
                idx,
                log_callback,
                preserve_audio=preserve_audio,
                add_music=add_music,
                normalize_audio=normalize_audio,
                edit_audio_db=edit_audio_db,
                audio_db=audio_db,
            )
        except Exception as e:
            _log(f"  [ERROR] Unexpected error: {e}")
            ok = False

        if ok:
            succeeded += 1
            results.append({"folder": folder_info["job_dir"], "status": "OK"})
        else:
            failed += 1
            results.append({"folder": folder_info["job_dir"], "status": "FAIL"})
            _log(f"  [!] Gagal: {Path(folder_info['job_dir']).name}")

    # Summary
    _log("=" * 50)
    _log(f"Selesai: {succeeded} berhasil, {failed} gagal dari {len(folders)} folder")
    _log("=" * 50)

    return {
        "success": succeeded > 0,
        "total": len(folders),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }
