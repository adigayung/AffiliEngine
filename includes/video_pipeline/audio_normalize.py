#!/usr/bin/env python3
"""normalize.py - Enhance and normalize audio of video/audio files using FFmpeg.

Default pipeline:
    Input video/audio
    → Extract audio to a temporary WAV at the *input* sample rate (FFmpeg)
    → Enhance voice (noisereduce + Pedalboard)
    → Two-pass EBU R128 loudness normalization + true-peak protection (FFmpeg)
    → Output video/audio (video stream copied, audio re-encoded to AAC 192k)

The "enhance voice" stage uses the `pedalboard` and `noisereduce` Python
packages and runs automatically as part of the standard pipeline. Because the
enhance stage already performs noise reduction (noisereduce + NoiseGate),
FFmpeg's `afftdn` is NOT applied on top of it (avoids double noise reduction /
loss of detail).

The video stream is always copied without re-encoding, preserving resolution,
frame rate, duration and A/V sync. The audio sample rate follows the input.

Usage:
    python normalize.py a.mp4
    python normalize.py a.mp4 -o hasil.mp4
    python normalize.py a.mp4 --target -14

Library usage (dipakai oleh video pipeline):
    from includes.video_pipeline.audio_normalize import normalize_video_file
    out = normalize_video_file("input.mp4", "output.mp4", log_callback=print)
    # -> path output bila berhasil, atau None bila dilewati/gagal.
"""

import argparse
import json
import logging
import multiprocessing
import shutil
import subprocess
import sys
import os
import tempfile


logger = logging.getLogger(__name__)


class AudioNormalizeError(RuntimeError):
    """Raised when the normalization pipeline cannot be completed.

    The CLI (``main``) converts this into a clean stderr message + exit code 1,
    so the module never calls ``sys.exit`` on a library code path.
    """


def _emit(message, log_callback=None, err=False):
    """Print a message and/or forward it to an optional log callback.

    When ``log_callback`` is provided (pipeline/UI usage) the message is routed
    there instead of stdout so the pipeline console shows it too. Otherwise the
    original CLI behaviour (print to stdout/stderr) is preserved.
    """
    if log_callback is not None:
        try:
            log_callback(str(message))
        except Exception:
            pass
    else:
        print(message, file=sys.stderr if err else sys.stdout)


DEFAULT_TARGET = -14.0
DEFAULT_TRUE_PEAK = -1.0
DEFAULT_LRA = 11.0
# afftdn noise reduction (dB) used only when the enhance backend is
# unavailable. On the normal (enhance) path afftdn is skipped because the
# enhance stage already reduces noise.
DEFAULT_NR = 3


# ---------------------------------------------------------------------------
# Optional "enhance voice" dependencies (pedalboard + noisereduce).
# Imported defensively so the CLI can still print --help / a clear error
# instead of dumping a raw traceback when the packages are missing.
# ---------------------------------------------------------------------------
try:
    from pedalboard import (
        NoiseGate,
        Compressor,
        LowShelfFilter,
        HighShelfFilter,
        HighpassFilter,
        Pedalboard,
    )
    from pedalboard.io import AudioFile
    import noisereduce as nr

    _ENHANCE_IMPORT_ERROR = None
except Exception as _exc:  # ImportError, or a numpy ABI mismatch, etc.
    _ENHANCE_IMPORT_ERROR = _exc


def check_enhance_deps():
    """Fail with a clear, actionable message if enhance deps are unavailable."""
    if _ENHANCE_IMPORT_ERROR is not None:
        print(
            "Error: the 'enhance voice' step requires the Python packages "
            "'pedalboard' and 'noisereduce', but they could not be imported.",
            file=sys.stderr,
        )
        print(f"       Detail: {_ENHANCE_IMPORT_ERROR}", file=sys.stderr)
        print("       Install them with:", file=sys.stderr)
        print(
            f"         {sys.executable} -m pip install pedalboard noisereduce",
            file=sys.stderr,
        )
        sys.exit(1)


def check_ffmpeg():
    """Ensure ffmpeg and ffprobe are available."""
    for cmd in ("ffmpeg", "ffprobe"):
        if shutil.which(cmd) is None:
            print(
                f"Error: '{cmd}' is not installed or not in PATH.",
                file=sys.stderr,
            )
            print(
                "Please install FFmpeg: https://ffmpeg.org/download.html",
                file=sys.stderr,
            )
            sys.exit(1)


def has_stream(filepath, stream_type):
    """Check if file has at least one stream of the given type ('a' or 'v')."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", stream_type,
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
        filepath,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() != ""


def has_audio(filepath):
    return has_stream(filepath, "a")


def has_video(filepath):
    return has_stream(filepath, "v")


def get_audio_sample_rate(filepath):
    """Return the sample rate (int Hz) of the first audio stream, or None."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        filepath,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    out = result.stdout.strip()
    if not out:
        return None
    try:
        return int(float(out))
    except ValueError:
        return None


def extract_audio_wav(input_path, wav_path, sample_rate, log_callback=None):
    """Extract the audio stream to a WAV file at the given sample rate.

    Raises:
        AudioNormalizeError: bila ffmpeg gagal mengekstrak audio.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", str(int(sample_rate)),
        wav_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = "\n".join(result.stderr.strip().splitlines()[-10:])
        raise AudioNormalizeError(
            "failed to extract audio to a temporary WAV file.\n" + detail
        )


def enhance_audio(raw_audio_path, enhanced_audio_path, sample_rate):
    """Enhance human voice in an audio file (noisereduce + Pedalboard).

    Chain:
        noisereduce.reduce_noise(stationary=True, prop_decrease=0.6)
        -> Pedalboard [
               HighpassFilter(80 Hz),                    # kill rumble below 80 Hz
               NoiseGate(-38 dB, ratio 2.5, release 400 ms),
               Compressor(-20 dB, ratio 2.5),
               LowShelfFilter(300 Hz, +4 dB, q 1),       # gentle vocal lift
               HighShelfFilter(1200 Hz, +1.5 dB, q 0.7),
           ]

    NOTE: The old fixed Gain(+13 dB) makeup is REMOVED. Loudness is handled by
    the two-pass EBU R128 loudnorm stage, which is applied AFTER this chain.
    A fixed +13 dB gain on top of loudnorm was amplifying the noise floor on
    silent segments.

    NoiseGate threshold was dropped to -38 dB (relative to a noise floor that
    is itself much lower after noisereduce + high-pass) so that speech above
    the (reduced) noise floor stays open while residual hiss on quiet segments
    is suppressed. Gate runs BEFORE any make-up/level gain.

    The input is read at `sample_rate` (which should be the file's own sample
    rate, so no unnecessary resampling occurs) and the result is written back
    at the same rate. Output is audio-only (no video).
    """
    # === Read audio (keep the requested sample rate) ===
    with AudioFile(raw_audio_path).resampled_to(sample_rate) as f:
        audio = f.read(f.frames)
        sr = f.samplerate

    # === Noise reduction (stationary) ===
    # noisereduce expects (channels, samples) for stereo; pedalboard's
    # AudioFile.read() already returns (channels, samples), so this is safe.
    reduced_noise = nr.reduce_noise(
        y=audio, sr=sr, stationary=True, prop_decrease=0.6
    )

    # Chain WITHOUT fixed makeup gain. Loudness is set by loudnorm afterwards.
    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=80),
        NoiseGate(threshold_db=-38, ratio=2.5, release_ms=400),
        Compressor(threshold_db=-20, ratio=2.5),
        LowShelfFilter(cutoff_frequency_hz=300, gain_db=4, q=1),
        HighShelfFilter(cutoff_frequency_hz=1200, gain_db=1.5, q=0.7),
    ])

    effected = board(reduced_noise, sr)

    # === Write enhanced audio to file ===
    with AudioFile(enhanced_audio_path, "w", sr, effected.shape[0]) as f:
        f.write(effected)


def _enhance_child(raw_audio_path, enhanced_audio_path, sample_rate):
    """Child-process entry point that runs ``enhance_audio``.

    Defined at module level so it can be pickled by the Windows 'spawn' start
    method. A Python-level failure exits non-zero without dumping a raw
    traceback; a native crash of pedalboard simply kills the child, which the
    parent detects via the exit code.
    """
    try:
        enhance_audio(raw_audio_path, enhanced_audio_path, sample_rate)
    except Exception as exc:  # defensive: keep the parent's output clean
        sys.stderr.write(f"enhance step failed: {exc}\n")
        sys.stderr.flush()
        os._exit(1)


def enhance_audio_isolated(raw_audio_path, enhanced_audio_path, sample_rate):
    """Run ``enhance_audio`` in a child process; return True on success.

    The pedalboard/noisereduce call is native code that can crash the whole
    interpreter on some systems. Running it in a child process lets the CLI
    detect the failure (via the exit code) and degrade gracefully instead of
    aborting with an access violation.
    """
    try:
        ctx = multiprocessing.get_context("spawn")
        proc = ctx.Process(
            target=_enhance_child,
            args=(raw_audio_path, enhanced_audio_path, sample_rate),
        )
        proc.start()
        proc.join()
        exitcode = proc.exitcode
    except Exception as exc:
        # multiprocessing unavailable -> try once in-process.
        print(
            f"  Warning: could not isolate the enhance step ({exc}); "
            "running it in-process.",
            file=sys.stderr,
        )
        try:
            enhance_audio(raw_audio_path, enhanced_audio_path, sample_rate)
            exitcode = 0
        except Exception as exc2:
            print(f"  Enhance step failed: {exc2}", file=sys.stderr)
            exitcode = 1

    return exitcode == 0 and os.path.isfile(enhanced_audio_path)


def extract_json(text):
    """Extract the last well-formed JSON object from a string by brace depth."""
    start = text.rfind("{")
    if start == -1:
        return None
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        return None
    return json.loads(text[start:end])


def measure_loudness(filepath, target_i, target_tp, target_lra, log_callback=None):
    """Run loudnorm analysis pass and return measured loudness values.

    Raises:
        AudioNormalizeError: bila ffmpeg gagal atau output JSON tidak terbaca.
    """
    filter_desc = (
        f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"
        f":print_format=json"
    )
    cmd = [
        "ffmpeg",
        "-i", filepath,
        "-af", filter_desc,
        "-f", "null",
        "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        detail = "\n".join(result.stderr.strip().splitlines()[-10:])
        raise AudioNormalizeError(
            "Error during loudness measurement pass.\n" + detail
        )

    data = extract_json(result.stderr)
    if data is None:
        raise AudioNormalizeError(
            "Could not parse loudness measurement output from FFmpeg."
        )

    return {
        "input_i": float(data["input_i"]),
        "input_tp": float(data["input_tp"]),
        "input_lra": float(data["input_lra"]),
        "input_thresh": float(data["input_thresh"]),
    }


def estimate_noise_floor(filepath, duration=3):
    """Estimate noise floor level using astats filter on a short sample.

    Analyzes the first `duration` seconds of audio to estimate the noise
    floor. The noise floor is approximated as the 10th percentile of RMS
    levels across all frames (the quietest non-silent frames).

    Returns the estimated noise floor in dB RMS, or None if estimation fails.
    """
    cmd = [
        "ffmpeg",
        "-i", filepath,
        "-t", str(duration),
        "-af", "astats=metadata=1:reset=1",
        "-f", "null",
        "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return None

    rms_levels = []
    for line in result.stderr.splitlines():
        if "RMS level dB" in line:
            try:
                rms = float(line.split("RMS level dB:")[1].strip())
                # Filter out near-silence frames (likely actual silence, not noise)
                if rms > -80:
                    rms_levels.append(rms)
            except (ValueError, IndexError):
                pass

    if len(rms_levels) < 10:
        return None

    # The noise floor is estimated as the 10th percentile of RMS levels
    # (the quietest 10% of non-silent frames are likely noise-dominated)
    rms_levels.sort()
    percentile_10 = rms_levels[int(len(rms_levels) * 0.1)]

    return percentile_10


def normalize(
    input_path,
    output_path,
    target_i,
    target_tp,
    target_lra,
    nr_amount,
    log_callback=None,
):
    """Run the enhanced + normalized output pipeline.

    Steps:
        1. Extract audio from `input_path` to a temp WAV at the input sample rate.
        2. Enhance voice (noisereduce + Pedalboard) — isolated in a child
           process; if the enhance backend is unusable, fall back to the plain
           FFmpeg pipeline so an output is still produced.
        3. Pass 1: measure integrated loudness of the (enhanced) audio.
        4. Pass 2: loudness-normalize (loudnorm) + true-peak protection, encode
           to AAC 192k, and mux with the (copied) video stream.

    All temporary files are removed afterwards, including on error.

    Returns (input_i, offset, enhance_used).
    """
    sample_rate = get_audio_sample_rate(input_path) or 44100
    video_present = has_video(input_path)

    temp_dir = tempfile.mkdtemp(prefix="normalize_")
    raw_wav = os.path.join(temp_dir, "input_raw.wav")
    enhanced_wav = os.path.join(temp_dir, "input_enhanced.wav")

    try:
        # --- Step 1: extract audio to WAV at the input sample rate ---
        _emit(f"Step 1/3: Extracting audio ({sample_rate} Hz)...", log_callback)
        extract_audio_wav(input_path, raw_wav, sample_rate, log_callback)

        # --- Step 2: enhance voice (isolated, degrades gracefully) ---
        _emit("Step 2/3: Enhancing voice...", log_callback)
        enhance_used = enhance_audio_isolated(raw_wav, enhanced_wav, sample_rate)

        if enhance_used:
            audio_for_norm = enhanced_wav
        else:
            msg = (
                "voice enhancement backend ('pedalboard'/'noisereduce') "
                "is not usable on this system; falling back to the plain FFmpeg "
                "pipeline (noise reduction + loudness normalization)."
            )
            logger.warning(msg)
            _emit("  Warning: " + msg, log_callback, err=True)
            audio_for_norm = raw_wav

        # --- Step 3, Pass 1: measure loudness of the audio to normalize ---
        _emit("Step 3/3: Measuring loudness...", log_callback)
        measured = measure_loudness(
            audio_for_norm, target_i, target_tp, target_lra, log_callback
        )

        input_i = measured["input_i"]
        input_tp = measured["input_tp"]
        input_lra = measured["input_lra"]
        input_thresh = measured["input_thresh"]

        # Estimate noise floor for better logging (works on both paths).
        noise_floor = estimate_noise_floor(audio_for_norm)
        if noise_floor is not None:
            _emit(
                f"  Estimated noise floor after enhancement: {noise_floor:.1f} dB RMS",
                log_callback,
            )

        # CRITICAL: offset MUST be 0 when using two-pass loudnorm with
        # measured values (measured_I, measured_TP, etc.). The measured
        # values already tell loudnorm exactly how much linear gain to
        # apply to hit the target (-30.2 -> -14 = +16.2 dB).
        # The 'offset' parameter is ADDITIONAL gain on TOP of that
        # normalization, which would DOUBLE the required gain and
        # drastically amplify the noise floor on quiet segments.
        # Fix: offset=0 to avoid double-gain / noise amplification.
        offset = 0.0
        total_gain_lu = target_i - input_i

        # Build the filter chain. When enhance ran, it already performed noise
        # reduction (noisereduce + NoiseGate + HighPass), so afftdn is skipped
        # to avoid double noise reduction. afftdn is only used on the fallback path.
        filters = []
        if not enhance_used and nr_amount > 0:
            # On the fallback path: more aggressive afftdn + adaptive gate
            # to suppress residual noise floor BEFORE loudnorm.
            nr_val = max(nr_amount, 8)
            # afftdn = adaptive frequency-domain noise reduction
            filters.append(f"afftdn=nr={nr_val}:tn=1")
            # agate = adaptive gate to keep noise floor down on quiet segments
            # threshold at -36 dB, ratio 3:1, fast attack (1ms), slower release (150ms)
            filters.append("agate=threshold=-36dB:ratio=3:attack=1:release=150")

        filters.append(
            f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"
            f":measured_I={input_i}:measured_TP={input_tp}"
            f":measured_LRA={input_lra}:measured_thresh={input_thresh}"
            f":offset={offset}:linear=true"
        )
        # +2 dB gain (linear = 10^(2/20) ≈ 1.26) before true-peak limiter
        filters.append("volume=1.26")
        # True-peak limiter at -1 dBTP (limit=0.995 ≈ -0.04 dBFS, combined with loudnorm TP=-1.0 gives ~-1 dBTP)
        filters.append("alimiter=limit=0.995:attack=5:release=50:level=true")

        filter_desc = ",".join(filters)

        # Pass 2: apply filters to the (enhanced) audio and mux with copied video.
        cmd = ["ffmpeg", "-y", "-i", input_path, "-i", audio_for_norm]

        if video_present:
            # Copy the video stream without re-encoding; take audio from the
            # processed WAV (input 1).
            cmd.extend(["-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy"])
        else:
            cmd.extend(["-map", "1:a:0"])

        # loudnorm internally works at 192 kHz, which would otherwise bump the
        # encoded rate; pin the output rate to the input sample rate.
        cmd.extend(["-af", filter_desc, "-ar", str(sample_rate)])
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        cmd.append(output_path)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            detail = "\n".join(result.stderr.strip().splitlines()[-10:])
            raise AudioNormalizeError(
                "Error during normalization pass.\n" + detail
            )

        return input_i, total_gain_lu, enhance_used
    finally:
        # Always clean up temporary WAV files, even on error.
        shutil.rmtree(temp_dir, ignore_errors=True)


def normalize_video_file(
    input_path,
    output_path=None,
    target_i=DEFAULT_TARGET,
    target_tp=DEFAULT_TRUE_PEAK,
    target_lra=DEFAULT_LRA,
    nr_amount=DEFAULT_NR,
    log_callback=None,
):
    """Normalize the audio of a media file, callable from other modules.

    This is the *library* entry point used by the video pipeline
    (``includes/video_pipeline/processor.py``). It wraps :func:`normalize` so
    that no ``sys.exit`` ever reaches the caller: failures are logged and
    reported as ``None`` so the pipeline can continue with the original file.

    Args:
        input_path: Path file video/audio input (mp4) yang akan dinormalisasi.
        output_path: Path output. Jika None, memakai ``<input>_normalized<ext>``.
        target_i: Target integrated loudness (LUFS).
        target_tp: Target true peak (dBTP).
        target_lra: Target loudness range (LU).
        nr_amount: Noise reduction afftdn (dB) untuk jalur fallback.
        log_callback: Optional callable(str) untuk meneruskan log ke UI.

    Returns:
        str path output normalisasi bila berhasil, atau ``None`` bila dilewati
        (tidak ada audio / ffmpeg tidak tersedia) atau gagal.
    """
    def _log(msg):
        _emit(msg, log_callback)

    input_path = str(input_path)

    if not os.path.isfile(input_path):
        _log(f"[FAIL] Normalize audio: input tidak ditemukan: {input_path}")
        return None

    # ffmpeg/ffprobe wajib; kalau tidak ada, jangan hentikan pipeline.
    for cmd in ("ffmpeg", "ffprobe"):
        if shutil.which(cmd) is None:
            _log(f"[WARN] Normalize audio: '{cmd}' tidak tersedia, dilewati")
            return None

    if not has_audio(input_path):
        _log("[SKIP] Normalize audio: tidak ada stream audio")
        return None

    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_normalized{ext}"
    output_path = str(output_path)

    try:
        input_i, total_gain_lu, enhance_used = normalize(
            input_path,
            output_path,
            target_i=target_i,
            target_tp=target_tp,
            target_lra=target_lra,
            nr_amount=nr_amount,
            log_callback=log_callback,
        )
    except AudioNormalizeError as exc:
        _log(f"[FAIL] Normalize audio gagal: {exc}")
        return None
    except Exception as exc:  # defensive: jangan crash-kan pipeline
        logger.exception("Normalize audio error for %s", input_path)
        _log(f"[FAIL] Normalize audio error: {exc}")
        return None

    if os.path.isfile(output_path) and os.path.getsize(output_path) > 0:
        sign = "+" if total_gain_lu >= 0 else ""
        logger.info(
            "Normalize audio: %s -> %s (%.1f LUFS -> %.1f LUFS, %s%.1f dB, "
            "enhance=%s)",
            input_path,
            output_path,
            input_i,
            target_i,
            sign,
            total_gain_lu,
            enhance_used,
        )
        _log(
            f"[OK] Normalize audio: {input_i:.1f} LUFS -> {target_i:.1f} LUFS "
            f"({sign}{total_gain_lu:.1f} dB)"
        )
        return output_path

    _log("[FAIL] Normalize audio: output tidak dihasilkan")
    return None


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Enhance and normalize audio of video/audio files: voice enhancement "
            "(noisereduce + Pedalboard) followed by two-pass EBU R128 loudness "
            "normalization to a target integrated loudness level (LUFS)."
        )
    )
    parser.add_argument("input", help="Input video or audio file")
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: <input>_normalized<ext>)",
    )
    parser.add_argument(
        "--target",
        type=float,
        default=DEFAULT_TARGET,
        help=f"Target integrated loudness in LUFS (default: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--nr",
        type=float,
        default=DEFAULT_NR,
        help=(
            f"Noise reduction amount in dB using afftdn (0=off, default: {DEFAULT_NR}). "
            "The enhance stage already performs noise reduction, so afftdn is "
            "skipped on the normal path; this value is used only when the "
            "enhance backend is unavailable."
        ),
    )

    args = parser.parse_args()

    check_ffmpeg()

    input_path = args.input

    if not os.path.isfile(input_path):
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not has_audio(input_path):
        print(f"Error: No audio stream found in: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Enhance voice is part of the default pipeline -> deps must be available.
    check_enhance_deps()

    # Log dependency versions for diagnostics.
    try:
        import pedalboard as _pd
        import noisereduce as _nr
        _pd_ver = getattr(_pd, "__version__", "?")
        _nr_ver = getattr(_nr, "__version__", "?")
        print(f"  Dependencies: pedalboard {_pd_ver}, noisereduce {_nr_ver}")
        print(f"  Python: {sys.version.split()[0]}, FFmpeg pipeline: enhance + two-pass loudnorm")
    except Exception:
        pass

    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_normalized{ext}"

    try:
        input_i, offset, enhance_used = normalize(
            input_path,
            output_path,
            target_i=args.target,
            target_tp=DEFAULT_TRUE_PEAK,
            target_lra=DEFAULT_LRA,
            nr_amount=args.nr,
        )
    except AudioNormalizeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    total_gain_lu = args.target - input_i  # negative if quieter, positive if louder
    sign = "+" if total_gain_lu >= 0 else ""
    print()
    print(f"Input: {input_path}")
    print(f"Original loudness: {input_i:.1f} LUFS")
    print(f"Target loudness: {args.target:.1f} LUFS")
    print(f"Adjustment: {sign}{total_gain_lu:.1f} dB (two-pass loudnorm, offset=0)")
    if enhance_used:
        print("Pipeline path: ENHANCE (noisereduce + Pedalboard -> two-pass loudnorm)")
    else:
        print("Pipeline path: FALLBACK (afftdn+agate -> two-pass loudnorm)")
        if args.nr > 0:
            print(f"Noise reduction: afftdn nr={args.nr} dB + agate (fallback)")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
