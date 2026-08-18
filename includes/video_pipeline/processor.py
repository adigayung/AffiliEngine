"""
processor.py — Orchestrates the entire video pipeline for a root folder.

Workflow:
  1. Scan root folder recursively for a.mp4 files.
  2. For each valid a.mp4 (with sound.json in same dir):
     a. decode_video(a.mp4) -> decode_output.mp4
     b. add_sound(decode_output.mp4, music.mp3) -> sound_output.mp4
     c. zoom_video(sound_output.mp4, 1.05) -> zoom_output.mp4
     d. upscale_video(zoom_output.mp4) -> upscale_output.mp4
     e. Move final output to job_dir/<name_from_schedule.json>
     f. Clean up temporary files (only pipeline-created files)
  3. Report progress via callback (for realtime logging)
"""

from pathlib import Path
from typing import Callable, Optional, List
import json
import shutil

from includes.video_pipeline.decode_video import decode_single_video
from includes.video_pipeline.add_sound import add_sound
from includes.video_pipeline.zoom_video import zoom_video
from includes.video_pipeline.upscale_video import upscale_video


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
) -> bool:
    """Process a single folder through the video pipeline.

    Args:
        folder_info: Dict with video_path, sound_json_path, asset_dir, job_dir.
        music_index: Round-robin index for music selection.
        log_callback: Optional function to call for realtime log messages.
        preserve_audio: Jika True, audio asli video dipertahankan.
        add_music: Jika True, music dari sound.json ditambahkan.

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
) -> dict:
    """Main entry point: process all videos in a root folder.

    Scans recursively for valid folders, runs the full pipeline on each,
    and reports results.

    Args:
        root_path: Absolute path to the root folder containing video projects.
        log_callback: Optional callable(text: str) for realtime log updates.
        preserve_audio: Jika True, audio asli video dipertahankan (default False).
        add_music: Jika True, music dari sound.json ditambahkan (default True).

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
