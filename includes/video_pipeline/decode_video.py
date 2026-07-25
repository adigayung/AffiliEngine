"""
decode_video.py — Decode/reverse a single video file.

This module wraps the root-level decode_video logic for use
inside the video_pipeline package.

Pipeline per video:
  Jika b.mp4 tersedia di folder yang sama:
    a.mp4 + DipToBlack(0.4s) + b.mp4 -> output.mp4
  Jika b.mp4 tidak tersedia:
    a.mp4
      |-- Reverse -> a_2.mp4
    a.mp4 + DipToBlack(0.4s) + a_2.mp4 -> output.mp4
"""

from pathlib import Path
from typing import Optional
import subprocess
import shutil
import cv2


# Konstanta
MIN_WIDTH = 1440
MIN_HEIGHT = 2560
VIDEO2X_PATH = r"./app/video2x-windows-amd64/video2x.exe"
SCALE_PERCENT = 1.05  # 105%
DIP_DURATION = 0.4    # detik transisi Dip To Black


def is_resolution_below(video_path: str, width: int = MIN_WIDTH, height: int = MIN_HEIGHT) -> bool:
    """Cek apakah resolusi video di bawah threshold yang ditentukan.

    Args:
        video_path: Path ke file video.
        width: Lebar minimum (default 1440).
        height: Tinggi minimum (default 2560).

    Returns:
        True jika resolusi di bawah threshold, False jika cukup atau gagal baca.
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return False

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.release()

    print(f"  Resolusi: {w}x{h}")

    return w < width or h < height


def _ffmpeg(cmd: list, description: str, timeout: int = 600) -> bool:
    """Helper untuk menjalankan FFmpeg dan menangani error.

    Args:
        cmd: List argumen FFmpeg (tanpa 'ffmpeg' di awal).
        description: Deskripsi langkah untuk log.
        timeout: Timeout dalam detik.

    Returns:
        True jika sukses, False jika gagal.
    """
    full_cmd = ["ffmpeg"] + cmd
    print(f"  {description}...")
    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            stderr_short = result.stderr[:300] if result.stderr else ""
            print(f"  {description} GAGAL: {stderr_short}")
            return False
        print(f"  {description} OK")
        return True
    except subprocess.TimeoutExpired:
        print(f"  {description} TIMEOUT")
        return False
    except FileNotFoundError:
        print("  ffmpeg tidak ditemukan. Pastikan ffmpeg terinstal.")
        return False
    except Exception as e:
        print(f"  {description} ERROR: {e}")
        return False


def _build_first_copy(video_file: Path) -> Optional[Path]:
    """Langkah 1: siapkan a_1.mp4 — upscale jika resolusi rendah, copy jika cukup.

    Args:
        video_file: Path ke a.mp4 asli.

    Returns:
        Path ke a_1.mp4 jika berhasil, None jika gagal.
    """
    a1_path = video_file.with_name("a_1.mp4")
    resolusi_below = is_resolution_below(str(video_file))

    if resolusi_below:
        # Upscale dengan Video2X
        print(f"  Upscaling: {video_file.name} -> {a1_path.name}")
        cmd = [
            str(VIDEO2X_PATH),
            "-i", str(video_file),
            "-o", str(a1_path),
            "-p", "realesrgan",
            "-s", "4",
            "--realesrgan-model", "realesr-animevideov3",
        ]
        try:
            result = subprocess.run(cmd, capture_output=False, text=True, timeout=600)
            file_ok = a1_path.exists() and a1_path.stat().st_size > 0
            if file_ok:
                if result.returncode != 0:
                    print(f"  Warning: Video2X exit code {result.returncode} "
                          f"tetapi output berhasil dibuat. Melanjutkan pipeline.")
                print(f"  Upscale berhasil: {a1_path}")
            else:
                print(f"  Upscale gagal (returncode={result.returncode}, "
                      f"output={'tidak ada' if not a1_path.exists() else '0 byte'})")
                return None
        except subprocess.TimeoutExpired:
            print("  Upscale timeout (>10 menit)")
            return None
        except FileNotFoundError:
            print(f"  Video2X tidak ditemukan di: {VIDEO2X_PATH}")
            return None
        except Exception as e:
            print(f"  Upscale error: {e}")
            return None
    else:
        # Copy langsung
        print(f"  Resolusi cukup, copy ke {a1_path.name}")
        try:
            shutil.copy2(str(video_file), str(a1_path))
            print(f"  Copy berhasil: {a1_path}")
        except Exception as e:
            print(f"  Copy gagal: {e}")
            return None

    return a1_path if a1_path.exists() else None


def _scale_105(input_path: Path) -> bool:
    """Langkah 2: Scale video 105% dengan canvas tetap 1440x2560.

    Efek yang dihasilkan sama seperti Adobe Premiere Pro:
    - Anchor point di tengah frame (bukan pojok kiri atas).
    - Video diperbesar 105% dari tengah.
    - Crop dilakukan simetris: kiri=kanan, atas=bawah.
    - Posisi subjek tidak bergeser (tidak ada shifting).

    Args:
        input_path: Path file video yang akan diproses.

    Returns:
        True jika berhasil, False jika gagal.
    """
    scaled_path = input_path.with_stem(input_path.stem + "_scaled")

    vf = (
        f"scale=trunc(iw*{SCALE_PERCENT}/2)*2:"
        f"trunc(ih*{SCALE_PERCENT}/2)*2:"
        f"flags=lanczos,"
        f"crop={MIN_WIDTH}:{MIN_HEIGHT}:"
        f"(in_w-{MIN_WIDTH})/2:"
        f"(in_h-{MIN_HEIGHT})/2"
    )

    cmd = [
        "-i",
        str(input_path),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-an",
        "-movflags",
        "+faststart",
        "-y",
        str(scaled_path),
    ]

    if not _ffmpeg(cmd, f"Scale 105% {input_path.name}"):
        return False

    # Safe replace
    try:
        if input_path.exists():
            input_path.unlink()
        scaled_path.rename(input_path)
        print(f"  [OK] Scale 105% OK: {input_path.name}")
        return True
    except Exception as e:
        print(f"  [FAIL] Rename gagal: {e}")
        try:
            if scaled_path.exists():
                scaled_path.unlink()
        except Exception:
            pass
    return False


def _reverse_video(input_path: Path, output_path: Path) -> bool:
    """Langkah: Reverse video menggunakan ffmpeg.

    Args:
        input_path: Path file video input.
        output_path: Path file video output.

    Returns:
        True jika berhasil, False jika gagal.
    """
    cmd = [
        "-i", str(input_path),
        "-vf", "reverse",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-an",
        "-y",
        str(output_path),
    ]

    return _ffmpeg(cmd, f"Reverse {input_path.name} -> {output_path.name}")


def _merge_dip_to_black(video_a: Path, video_b: Path, output_path: Path) -> bool:
    """Gabung dua video dengan transisi Dip To Black.

    Dip To Black = crossfade dengan black color (fade out lalu fade in).

    Args:
        video_a: Path video pertama (a.mp4).
        video_b: Path video kedua.
        output_path: Path output (output.mp4).

    Returns:
        True jika berhasil, False jika gagal.
    """
    import json

    # Probe durasi video_a
    probe_cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(video_a),
    ]
    try:
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        if probe_result.returncode != 0:
            print("  Probe gagal, fallback ke hard cut")
            return _concat_fallback(video_a, video_b, output_path)
        probe_data = json.loads(probe_result.stdout)
        duration_a = float(probe_data.get("format", {}).get("duration", 0))
    except Exception as e:
        print(f"  Probe error: {e}, fallback ke hard cut")
        return _concat_fallback(video_a, video_b, output_path)

    if duration_a <= 0:
        print("  Durasi video_a tidak valid, fallback ke hard cut")
        return _concat_fallback(video_a, video_b, output_path)

    dip = DIP_DURATION
    start_fade_out = max(0, duration_a - dip)

    cmd = [
        "-i", str(video_a),
        "-i", str(video_b),
        "-filter_complex",
        f"[0:v]fade=t=out:st={start_fade_out}:d={dip}:color=black[f0];"
        f"[1:v]fade=t=in:st=0:d={dip}:color=black[f1];"
        f"[f0][f1]concat=n=2:v=1:a=0[out]",
        "-map", "[out]",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-y",
        str(output_path),
    ]

    return _ffmpeg(cmd, f"Merge with Dip To Black ({dip}s)")


def _concat_fallback(video_a: Path, video_b: Path, output_path: Path) -> bool:
    """Fallback: concat dua video tanpa transisi (hard cut).

    Args:
        video_a: Path video pertama.
        video_b: Path video kedua.
        output_path: Path output.

    Returns:
        True jika berhasil, False jika gagal.
    """
    cmd = [
        "-i", str(video_a),
        "-i", str(video_b),
        "-filter_complex",
        "[0:v][1:v]concat=n=2:v=1:a=0[out]",
        "-map", "[out]",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-y",
        str(output_path),
    ]

    return _ffmpeg(cmd, "Merge (hard cut fallback)")


def decode_single_video(video_path: str) -> Optional[str]:
    """Proses decode/reverse untuk SATU file video.

    Pipeline:
      Jika b.mp4 tersedia di folder yang sama:
        1. a.mp4 + DipToBlack(0.4s) + b.mp4 -> <parent>/output.mp4
      Jika b.mp4 tidak tersedia:
        1. a.mp4 -> Reverse -> a_2.mp4
        2. a.mp4 + DipToBlack(0.4s) + a_2.mp4 -> <parent>/output.mp4

    Args:
        video_path: Path absolut ke file a.mp4.

    Returns:
        Path absolut ke output.mp4 jika berhasil, None jika gagal.
    """
    video_file = Path(video_path)

    if not video_file.exists() or not video_file.is_file():
        print(f"  [!] Video tidak ditemukan: {video_path}")
        return None

    # Cek apakah b.mp4 ada di folder yang sama
    b_path = video_file.with_name("b.mp4")
    second_video_exists = b_path.exists() and b_path.is_file()

    if second_video_exists:
        print(f"  [INFO] b.mp4 ditemukan, menggunakan b.mp4 sebagai video kedua")
    else:
        print(f"  [INFO] b.mp4 tidak ditemukan, membuat reverse video (a_2.mp4)")

    # Step 1: Siapkan video kedua
    if second_video_exists:
        # Gunakan b.mp4 langsung sebagai video kedua
        second_video_path = b_path
    else:
        # Reverse a.mp4 -> a_2.mp4
        a2_path = video_file.with_name("a_2.mp4")
        if not _reverse_video(video_file, a2_path):
            print(f"  [!] Gagal reverse, skip")
            if a2_path.exists():
                try:
                    a2_path.unlink()
                except Exception:
                    pass
            return None
        second_video_path = a2_path

    # Step 2: Merge a.mp4 + DipToBlack(0.4s) + second_video -> output.mp4
    output_path = video_file.with_name("output.mp4")
    if not _merge_dip_to_black(video_file, second_video_path, output_path):
        print(f"  [!] Gagal merge, skip")
        return None

    return str(output_path.resolve())
