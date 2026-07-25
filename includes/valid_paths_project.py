# File : includes\valid_paths_project.py
import json
import os


def valid_paths_project(file):

    if file is None:
        raise ValueError("File tidak ditemukan.")

    try:
        workflow = json.load(file)
    except Exception:
        raise ValueError("Format JSON tidak valid.")

    folders = workflow.get("folders")

    if not isinstance(folders, list):
        raise ValueError("Field 'folders' tidak valid.")

    paths = []

    for folder in folders:

        if not isinstance(folder, dict):
            continue

        path = folder.get("path", "").strip()

        if not path:
            continue

        if not os.path.isdir(path):
            continue

        schedule_file = os.path.join(path, "schedule.json")

        if os.path.isfile(schedule_file):

            with open(schedule_file, "r", encoding="utf-8") as f:
                schedule = json.load(f)

            if schedule.get("schedule", {}).get("status") == "pending":

                video_name = schedule.get("files", {}).get("video")

                if not video_name:
                    continue

                video_path = os.path.join(path, video_name)

                if not os.path.isfile(video_path):
                    continue

                # Skip jika ukuran video kurang dari 1 MB
                if os.path.getsize(video_path) < 1024 * 1024:
                    continue

                paths.append(path)

    return paths