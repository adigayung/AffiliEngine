"""
add_sound.py — Add an audio track to a video without re-encoding the video stream.
"""

from pathlib import Path
from typing import Optional
import subprocess
import json


def _get_duration_seconds(file_path: Path) -> Optional[float]:
    """Get duration of a media file in seconds using ffprobe.

    Args:
        file_path: Path to the media file.

    Returns:
        Duration in seconds, or None if it fails.
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(file_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        duration = data.get("format", {}).get("duration")
        if duration is None:
            return None
        return float(duration)
    except Exception:
        return None


def _has_audio_stream(file_path: Path) -> bool:
    """Check whether a media file has an audio stream.

    Args:
        file_path: Path to the media file.

    Returns:
        True if an audio stream exists, False otherwise.
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
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "audio":
                return True
        return False
    except Exception:
        return False


def add_sound(
    video_path: str,
    audio_path: str,
    preserve_audio: bool = False,
) -> Optional[str]:
    """Add an audio track to a video without re-encoding the video.

    The video stream is preserved as-is (copy). Audio is encoded as AAC.

    Jika preserve_audio=False (default): audio asli video dihapus dan hanya
    music (audio_path) yang digunakan sebagai audio. Perilaku existing.
    Jika audio lebih panjang dari video, audio dipotong sesuai durasi video.

    Jika preserve_audio=True dan video memiliki audio asli: audio asli dan
    music DICAMPUR (amix), keduanya tetap terdengar. Durasi mengikuti audio
    asli video (duration=first) sehingga tidak melebihi durasi video.

    Args:
        video_path: Path to the input video file.
        audio_path: Path to the input audio file.
        preserve_audio: Jika True, audio asli video dipertahankan dan
            dicampur dengan music.

    Returns:
        Path to the output video file with sound, or None on failure.
    """
    video = Path(video_path)
    audio = Path(audio_path)

    # Validate inputs
    if not video.exists():
        print("  [FAIL] Video tidak ditemukan")
        return None

    if not audio.exists():
        print("  [FAIL] Audio tidak ditemukan")
        return None

    # Build output path: <video_name>_sound.mp4
    output_path = video.with_stem(video.stem + "_sound")

    # Get durations
    video_duration = _get_duration_seconds(video)
    audio_duration = _get_duration_seconds(audio)

    if video_duration is None:
        print("  [FAIL] Gagal membaca durasi video")
        return None

    if audio_duration is None:
        print("  [FAIL] Gagal membaca durasi audio")
        return None

    if preserve_audio and _has_audio_stream(video):
        # Kondisi B: audio asli video + music dicampur (bukan menggantikan).
        # duration=first -> durasi hasil ikut audio asli video (durasi video),
        # sehingga music tidak memperpanjang video.
        cmd: list[str] = [
            "ffmpeg",
            "-i", str(video),
            "-i", str(audio),
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "0:v:0",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-t", str(video_duration),
            "-y", str(output_path),
        ]
    else:
        # Kondisi A: hanya music (perilaku existing).
        # Jika preserve_audio=True tapi video tidak punya audio, hasilnya
        # sama dengan existing: hanya music yang ditambahkan.
        cmd = [
            "ffmpeg",
            "-i", str(video),
            "-i", str(audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
        ]

        # If audio is longer than video, trim audio to video duration
        if audio_duration > video_duration:
            cmd.extend(["-t", str(video_duration)])

    cmd.extend(["-y", str(output_path)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=None)
        if result.returncode != 0:
            print("  [FAIL] FFmpeg gagal")
            return None
    except FileNotFoundError:
        print("  [FAIL] FFmpeg tidak ditemukan")
        return None
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return None

    if output_path.exists() and output_path.stat().st_size > 0:
        return str(output_path)

    print("  [FAIL] Output tidak ditemukan")
    return None
