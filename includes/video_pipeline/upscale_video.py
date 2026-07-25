"""
upscale_video.py — Upscale a single video using Video2X.
"""

from pathlib import Path
from typing import Optional
import subprocess


VIDEO2X_PATH = Path(__file__).resolve().parent.parent.parent / "app" / "video2x-windows-amd64" / "video2x.exe"


def upscale_video(video_path: str) -> Optional[str]:
    """Upscale a video using Video2X.

    Args:
        video_path: Path to the input video file.

    Returns:
        Path to the upscaled video if successful, None otherwise.
    """
    input_path = Path(video_path)

    if not input_path.exists():
        print(f"  [FAIL] Video tidak ditemukan: {video_path}")
        return None

    # Build output path by inserting "_upscale" before the extension
    output_path = input_path.with_stem(input_path.stem + "_upscale")

    print(f"  Upscaling: {input_path.name} -> {output_path.name}")

    try:
        result = subprocess.run(
            [
                str(VIDEO2X_PATH),
                "-i", str(input_path),
                "-o", str(output_path),
                "-p", "realesrgan",
                "-s", "2",
                "--realesrgan-model", "realesr-animevideov3",
            ],
            capture_output=False,
            text=True,
            timeout=None,
        )
    except FileNotFoundError:
        print(f"  [FAIL] Video2X tidak ditemukan di: {VIDEO2X_PATH}")
        return None
    except Exception as e:
        print(f"  [FAIL] Upscale error: {e}")
        return None

    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"  Upscale selesai: {output_path.name}")
        return str(output_path)

    print("  [FAIL] Upscale gagal.")
    return None
