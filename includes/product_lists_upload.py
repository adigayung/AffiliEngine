import os
import json


def open_product_lists(paths):
    """
    Menerima daftar path folder (dipisah newline),
    membaca schedule.json di setiap folder dan
    upload_schedule.json di folder parent,
    mengembalikan list dict berisi data untuk gallery.

    Setiap item:
    {
        "index": int (1-based),
        "folder": str,
        "image": str (full path to product/1.jpg),
        "exists": bool,
        "product_id": str or None,
        "title": str or None,
        "url": str or None
    }
    """
    if not paths:
        return []

    # --- Baca upload_schedule.json untuk mapping path -> product_id ---
    # Cari di folder parent dari path pertama
    folder_paths = []
    for line in paths.splitlines():
        folder = line.strip()
        if folder:
            folder_paths.append(folder)

    if not folder_paths:
        return []

    # Cari upload_schedule.json di parent folder dari path pertama
    parent_dir = os.path.dirname(folder_paths[0])
    path_to_product_id = {}
    upload_schedule_path = os.path.join(parent_dir, "upload_schedule.json")
    if os.path.exists(upload_schedule_path):
        try:
            with open(upload_schedule_path, "r", encoding="utf-8") as f:
                batch_data = json.load(f)
            for f_item in batch_data.get("folders", []):
                fpath = f_item.get("path", "")
                pid = f_item.get("product_id")
                if fpath and pid:
                    path_to_product_id[fpath] = pid
        except (json.JSONDecodeError, IOError):
            pass

    # --- Proses setiap folder ---
    result = []

    for idx, folder in enumerate(folder_paths, start=1):

        # Baca schedule.json
        schedule_path = os.path.join(folder, "schedule.json")
        title = None
        url = None

        if os.path.exists(schedule_path):
            try:
                with open(schedule_path, "r", encoding="utf-8") as f:
                    schedule_data = json.load(f)
                product_data = schedule_data.get("product", {})
                title = product_data.get("title")
                url = product_data.get("url")
            except (json.JSONDecodeError, IOError):
                pass

        # Cari image produk
        image_path = os.path.join(folder, "product", "1.jpg")
        exists = os.path.exists(image_path)

        # product_id dari upload_schedule.json
        product_id = path_to_product_id.get(folder)

        result.append({
            "index": idx,
            "folder": folder,
            "image": image_path,
            "exists": exists,
            "product_id": product_id,
            "title": title,
            "url": url
        })

    return result
