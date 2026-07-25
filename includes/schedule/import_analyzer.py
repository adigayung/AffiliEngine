# File : includes/schedule/import_analyzer.py
"""
Pattern Analyzer untuk Import Schedule.

Membaca file upload_schedule.json,
mengekstrak pola jadwal (datetime dari setiap folder),
mendeteksi pola berulang dengan algoritma Smart Pattern Detection,
dan mengembalikan representasi pattern yang ringkas (Pattern Compression).

KONSEP:
- upload_schedule.json -> Pattern Analyzer -> Smart Pattern Detection -> Pattern Editor
- Bukan menampilkan JSON mentah, tetapi mengekstrak PATTERN jadwal
- Pattern dikompresi: bagian berulang hanya ditampilkan sekali
- Tidak berasumsi weekly (7 hari) - mencari pattern terkecil (1-30 hari)
- Menghasilkan Initial Pattern + Repeat Pattern yang kaya informasi
"""

import json
from pathlib import Path
from datetime import datetime
from collections import OrderedDict


def analyze_upload_schedule(file_path: str) -> dict:
    """
    Membaca file upload_schedule.json dan menganalisis pola jadwal.
    """
    try:
        filepath = Path(file_path)
        if not filepath.exists():
            return {
                "success": False,
                "error": f"File tidak ditemukan: {file_path}"
            }

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return _analyze_json_data(data)

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Format JSON tidak valid: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error membaca file: {str(e)}"
        }


def analyze_upload_schedule_from_data(data: dict) -> dict:
    """
    Menganalisis pola jadwal dari data JSON yang sudah di-parse.
    """
    try:
        return _analyze_json_data(data)
    except Exception as e:
        return {
            "success": False,
            "error": f"Error menganalisis data: {str(e)}"
        }


def _analyze_json_data(data: dict) -> dict:
    """
    Core analyzer: extracts datetime from folders, builds daily schedule,
    and performs smart pattern detection.
    """
    folders = data.get("folders", [])
    if not folders:
        return {
            "success": False,
            "error": "Tidak ada folder dalam data JSON."
        }

    # ==============================
    # EKSTRAK DATETIME DARI FOLDERS
    # ==============================
    daily_map = OrderedDict()

    for folder in folders:
        dt_str = folder.get("datetime", "")
        if not dt_str:
            continue

        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

        date_key = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M")

        if date_key not in daily_map:
            daily_map[date_key] = {
                "date": date_key,
                "day_number": 0,
                "times": []
            }

        if time_str not in daily_map[date_key]["times"]:
            daily_map[date_key]["times"].append(time_str)

    # Urutkan berdasarkan tanggal
    sorted_dates = sorted(daily_map.keys())
    daily_schedule = []
    for idx, date_key in enumerate(sorted_dates, start=1):
        day_data = daily_map[date_key]
        day_data["day_number"] = idx
        day_data["times"].sort()
        daily_schedule.append(day_data)

    total_days = len(daily_schedule)
    total_uploads = sum(len(day["times"]) for day in daily_schedule)

    # ==============================
    # SMART PATTERN DETECTION
    # ==============================
    day_patterns = [tuple(day["times"]) for day in daily_schedule]

    pattern_result = _smart_detect_pattern(day_patterns)

    # Kumpulkan semua jam unik
    all_times = set()
    for day in daily_schedule:
        for t in day["times"]:
            all_times.add(t)
    all_times_sorted = sorted(all_times)

    # Bangun initial_pattern dan repeat_pattern untuk UI
    initial_pattern_days = []
    if pattern_result["initial_days"] > 0:
        for i in range(pattern_result["initial_days"]):
            initial_pattern_days.append({
                "day": i + 1,
                "times": list(day_patterns[i])
            })

    repeat_pattern_days = []
    if pattern_result["repeat_pattern"]:
        for i, times_tuple in enumerate(pattern_result["repeat_pattern"]):
            repeat_pattern_days.append({
                "day": i + 1,
                "times": list(times_tuple)
            })

    # Buat deskripsi
    initial_desc = ""
    if pattern_result["initial_days"] > 0:
        initial_desc = f"{pattern_result['initial_days']} hari unik sebagai initial pattern"

    repeat_desc = ""
    if pattern_result["repeat_days"] > 0 and pattern_result["total_repeats"] > 0:
        if pattern_result["repeat_days"] == 1:
            repeat_desc = f"Setiap hari ({pattern_result['total_repeats']}x)"
        elif pattern_result["repeat_days"] == 7:
            repeat_desc = f"Mingguan ({pattern_result['total_repeats']}x)"
        else:
            repeat_desc = f"Setiap {pattern_result['repeat_days']} hari ({pattern_result['total_repeats']}x)"

    compression_ratio = 0
    if pattern_result["initial_days"] + pattern_result["repeat_days"] > 0:
        displayed = pattern_result["initial_days"] + pattern_result["repeat_days"]
        compression_ratio = round((1 - displayed / total_days) * 100, 1) if total_days > 0 else 0

    return {
        "success": True,
        "error": None,
        "total_uploads": total_uploads,
        "total_days": total_days,
        "daily_schedule": daily_schedule,
        "pattern": {
            "type": pattern_result["type"],
            "initial_pattern": initial_pattern_days,
            "repeat_pattern": repeat_pattern_days,
            "repeat_every_days": pattern_result["repeat_days"],
            "repeat_start_day": pattern_result["initial_days"] + 1 if pattern_result["initial_days"] > 0 else 1,
            "repeat_count": pattern_result["total_repeats"],
            "total_pattern_length": pattern_result["initial_days"] + pattern_result["repeat_days"],
            "all_times_sorted": all_times_sorted,
            "initial_description": initial_desc,
            "repeat_description": repeat_desc,
            "initial_days": pattern_result["initial_days"],
            "unused_tail": pattern_result["unused_tail"]
        },
        "analysis": {
            "status": "success" if pattern_result["type"] != "unique" else "partial",
            "message": _generate_analysis_message(pattern_result),
            "pattern_found": pattern_result["type"] != "unique",
            "compression_ratio": compression_ratio,
            "total_uploads": total_uploads,
            "total_days": total_days,
            "pattern_length": pattern_result["initial_days"] + pattern_result["repeat_days"]
        }
    }


def _smart_detect_pattern(day_patterns: list) -> dict:
    """
    Smart Pattern Detection Algorithm.

    Mencari pola terkecil (1-30 hari) yang mampu menjelaskan seluruh jadwal.
    Tidak berasumsi weekly.
    Mampu mendeteksi:
    - Full repeat (1 hari berulang)
    - Initial + repeat
    - Multi-segment repeat (misal 5 hari, 11 hari, dll)
    - Unique (tidak ada pola)
    """
    total_days = len(day_patterns)

    if total_days == 0:
        return {
            "type": "unique",
            "initial_days": 0,
            "repeat_days": 0,
            "repeat_pattern": [],
            "total_repeats": 0,
            "unused_tail": 0
        }

    if total_days == 1:
        return {
            "type": "full_repeat",
            "initial_days": 0,
            "repeat_days": 1,
            "repeat_pattern": [day_patterns[0]],
            "total_repeats": 1,
            "unused_tail": 0
        }

    # ==============================
    # PHASE 1: Cari Full Repeat (1 hari)
    # ==============================
    first_pattern = day_patterns[0]
    if all(p == first_pattern for p in day_patterns):
        return {
            "type": "full_repeat",
            "initial_days": 0,
            "repeat_days": 1,
            "repeat_pattern": [first_pattern],
            "total_repeats": total_days,
            "unused_tail": 0
        }

    # ==============================
    # PHASE 2: Cari best pattern (initial + repeat)
    # Cari dari yang paling sederhana (pattern terkecil)
    # ==============================
    best_result = None
    best_score = float('inf')

    # Coba berbagai kombinasi initial_days (0 sampai setengah total)
    max_initial = min(total_days // 2, 30)

    for initial in range(0, max_initial + 1):
        remaining = total_days - initial
        if remaining < 2:
            continue

        # Coba berbagai panjang pattern (1 sampai setengah remaining)
        for pattern_len in range(1, min(remaining // 2 + 1, 31)):
            if remaining < pattern_len * 2:
                continue

            pattern = day_patterns[initial:initial + pattern_len]

            # Verifikasi bahwa pattern ini benar-benar berulang
            repeat_count = _count_repeats(day_patterns, initial, pattern)

            if repeat_count >= 2:
                used_days = initial + repeat_count * pattern_len
                unused_tail = total_days - used_days

                # Hitung score: semakin kecil semakin baik
                # Prioritaskan: 1) initial kecil, 2) pattern kecil, 3) banyak repeat
                score = (initial * 10) + pattern_len - (repeat_count * 2)

                if score < best_score:
                    best_score = score
                    best_result = {
                        "type": "mixed",
                        "initial_days": initial,
                        "repeat_days": pattern_len,
                        "repeat_pattern": pattern,
                        "total_repeats": repeat_count,
                        "unused_tail": unused_tail
                    }

    if best_result:
        return best_result

    # ==============================
    # PHASE 3: Fallback - semua unik
    # ==============================
    return {
        "type": "unique",
        "initial_days": total_days,
        "repeat_days": 0,
        "repeat_pattern": [],
        "total_repeats": 0,
        "unused_tail": 0
    }


def _count_repeats(day_patterns: list, start_idx: int, pattern: list) -> int:
    """
    Menghitung berapa kali pattern berulang dalam day_patterns,
    dimulai dari start_idx.
    """
    pattern_len = len(pattern)
    if pattern_len == 0:
        return 0

    total_days = len(day_patterns)
    repeat_count = 0
    pos = start_idx

    while pos + pattern_len <= total_days:
        if day_patterns[pos:pos + pattern_len] == pattern:
            repeat_count += 1
            pos += pattern_len
        else:
            break

    return repeat_count


def _generate_analysis_message(pattern_result: dict) -> str:
    """
    Generate human-readable message about the detected pattern.
    """
    ptype = pattern_result["type"]

    if ptype == "full_repeat":
        days_text = "setiap hari" if pattern_result["repeat_days"] == 1 else f"setiap {pattern_result['repeat_days']} hari"
        return (
            f"Pattern Sempurna Terdeteksi!\n"
            f"Semua jadwal ({pattern_result['total_repeats']} hari) mengulang pattern yang sama {days_text}."
        )

    elif ptype == "mixed":
        msg_parts = ["Pattern Berhasil Terdeteksi!\n"]
        if pattern_result["initial_days"] > 0:
            msg_parts.append(
                f"Analyzer menemukan:\n"
                f"- Initial Pattern: {pattern_result['initial_days']} hari pertama (pembuka)\n"
                f"- Repeat Pattern: {pattern_result['repeat_days']} hari (berulang {pattern_result['total_repeats']}x)"
            )
        else:
            msg_parts.append(
                f"Analyzer menemukan:\n"
                f"- Pattern: {pattern_result['repeat_days']} hari\n"
                f"- Berulang: {pattern_result['total_repeats']} kali"
            )

        if pattern_result["unused_tail"] > 0:
            msg_parts.append(f"- Sisa: {pattern_result['unused_tail']} hari (tidak termasuk pola)")

        msg_parts.append("\nPattern akan diulang sampai seluruh video habis.")
        return "\n".join(msg_parts)

    else:
        return (
            "Pattern Tidak Terdeteksi\n"
            "Seluruh jadwal bersifat unik (tidak ada pola berulang).\n"
            "Anda tetap dapat mengedit dan menggunakan jadwal ini."
        )


def generate_schedule_from_pattern(
    pattern_dict: dict,
    total_products: int,
    times: list
) -> list:
    """
    Menghasilkan daftar waktu upload dari hasil pattern analysis (versi baru).

    Args:
        pattern_dict: Hasil pattern analysis (dict dengan initial_pattern, repeat_pattern, dll)
        total_products: Jumlah produk yang akan dijadwalkan
        times: Daftar jam upload yang tersedia (sorted) - cadangan

    Returns:
        list of str: Daftar waktu dalam format "HH:MM"
    """
    if not times:
        return []

    initial_pattern = pattern_dict.get("initial_pattern", [])
    repeat_pattern = pattern_dict.get("repeat_pattern", [])
    pattern_type = pattern_dict.get("type", "unique")

    schedule_times = []

    def _extract_times_from_pattern(pattern_days):
        result = []
        for day in pattern_days:
            day_times = day.get("times", [])
            day_times = sorted(day_times)
            for t in day_times:
                result.append(t)
        return result

    # Proses initial pattern
    initial_times = _extract_times_from_pattern(initial_pattern)
    for t in initial_times:
        if len(schedule_times) < total_products:
            schedule_times.append(t)
        else:
            break

    if len(schedule_times) >= total_products:
        return schedule_times

    # Proses repeat pattern
    repeat_times = _extract_times_from_pattern(repeat_pattern)

    if not repeat_times:
        while len(schedule_times) < total_products:
            for t in times:
                if len(schedule_times) < total_products:
                    schedule_times.append(t)
        return schedule_times

    # Loop repeat pattern sampai semua produk terjadwal
    while len(schedule_times) < total_products:
        for t in repeat_times:
            if len(schedule_times) < total_products:
                schedule_times.append(t)
            else:
                break

    return schedule_times


def calculate_day_offset_from_pattern(import_data, product_idx):
    """
    Menghitung hari ke berapa (offset) untuk produk ke-product_idx
    berdasarkan pattern data (initial_pattern + repeat_pattern).
    """
    initial_pattern = import_data.get("initial_pattern", [])
    repeat_pattern = import_data.get("repeat_pattern", [])
    if not initial_pattern and not repeat_pattern:
        return 0
    initial_slots = sum(len(d.get("times", [])) for d in initial_pattern)
    repeat_slots = sum(len(d.get("times", [])) for d in repeat_pattern)
    if product_idx < initial_slots:
        cum = 0
        for d_idx, day in enumerate(initial_pattern):
            cum += len(day.get("times", []))
            if product_idx < cum:
                return d_idx
        return 0
    elif repeat_slots > 0:
        remaining = product_idx - initial_slots
        cycle = remaining // repeat_slots
        offset_in_cycle = remaining % repeat_slots
        cum = 0
        for d_idx, day in enumerate(repeat_pattern):
            cum += len(day.get("times", []))
            if offset_in_cycle < cum:
                return len(initial_pattern) + cycle * len(repeat_pattern) + d_idx
        return len(initial_pattern) + cycle * len(repeat_pattern)
    else:
        return 0
