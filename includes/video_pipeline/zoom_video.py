"""
zoom_video.py — Zoom (scale & center-crop) a video to remove watermark edges.

Efek identik dengan Adobe Premiere Pro:
  Motion → Scale = 105%
  - Video diperbesar, canvas tetap
  - Pinggir frame terpotong (watermark di pojok keluar frame)
  - Tidak ada padding hitam, stretch, atau perubahan resolusi
"""

from pathlib import Path
from typing import Optional
import subprocess
import json


def _get_video_resolution(video_path: str) -> Optional[tuple[int, int]]:
    """Get video width and height using ffprobe.

    Args:
        video_path: Path to the video file.

    Returns:
        (width, height) tuple, or None if failed.
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        str(video_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        if not streams:
            return None
        w = int(streams[0].get("width", 0))
        h = int(streams[0].get("height", 0))
        if w <= 0 or h <= 0:
            return None
        return (w, h)
    except Exception:
        return None


def zoom_video(video_path: str, scale: float = 1.05) -> str:
    """Perbesar video dengan scale factor lalu center-crop ke resolusi asli.

    Efek identik dengan Adobe Premiere Pro Motion → Scale.
    Watermark di pojok frame akan keluar dari frame setelah diperbesar.

    Args:
        video_path: Path ke file video input.
        scale: Faktor perbesaran (default 1.05 = 105%).

    Returns:
        Path ke file video hasil zoom.

    Raises:
        FileNotFoundError: Jika video input tidak ditemukan.
        ValueError: Jika resolusi tidak terbaca atau scale tidak valid.
        RuntimeError: Jika ffmpeg gagal.
    """
    input_path = Path(video_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Video tidak ditemukan: {video_path}")

    if scale <= 1.0:
        raise ValueError(f"Scale harus > 1.0, got {scale}")

    # Baca resolusi asli
    resolution = _get_video_resolution(video_path)
    if resolution is None:
        raise ValueError(f"Gagal membaca resolusi video: {video_path}")

    orig_width, orig_height = resolution

    # Bangun nama output: input_zoom.mp4
    output_path = input_path.with_stem(input_path.stem + "_zoom")

    # Filter: scale 105% lalu center-crop ke ukuran asli
    # scale=trunc(iw*scale/2)*2 memastikan dimensi genap (required encoder)
    vf = (
        f"scale=trunc(iw*{scale}/2)*2:trunc(ih*{scale}/2)*2:flags=lanczos,"
        f"crop={orig_width}:{orig_height}:"
        f"(in_w-{orig_width})/2:(in_h-{orig_height})/2"
    )

    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-y",
        str(output_path),
    ]

    print(f"  [Zoom] Scale {int(scale*100)}%")
    print(f"  [Zoom] Input  : {input_path.resolve()}")
    print(f"  [Zoom] Output : {output_path.resolve()}")
    print(f"  [Zoom] Resolusi: {orig_width}x{orig_height} -> scale {scale:.2f}x -> crop center")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Zoom timeout (>10 menit) untuk: {video_path}")
    except FileNotFoundError:
        raise RuntimeError("ffmpeg tidak ditemukan. Pastikan ffmpeg terinstal.")
    except Exception as e:
        raise RuntimeError(f"Error saat menjalankan ffmpeg: {e}")

    if result.returncode != 0:
        stderr_short = result.stderr[:500] if result.stderr else ""
        raise RuntimeError(
            f"Zoom gagal (ffmpeg exit code {result.returncode}): {stderr_short}"
        )

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"Zoom gagal: output tidak ditemukan atau 0 bytes")

    print(f"  [OK] Zoom {int(scale*100)}%")

    return str(output_path.resolve())
