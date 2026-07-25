import os
from includes.logFX import logger

def clear_files_in_path(temp_path="./temp"):
    """
    Menghapus semua file di dalam folder ./temp
    Tidak menghapus subfolder maupun isi subfolder.
    """
    if not os.path.exists(temp_path):
        logger("warning", f"Folder tidak ditemukan: {temp_path}")
        return

    deleted = 0

    for item in os.listdir(temp_path):
        file_path = os.path.join(temp_path, item)

        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                deleted += 1
                logger("debug", f"Deleted: {file_path}")
            except Exception as e:
                logger("debug", f"Gagal menghapus {file_path}: {e}")

    logger("info", f"\nSelesai. Total file dihapus: {deleted}")


if __name__ == "__main__":
    clear_files_in_path()