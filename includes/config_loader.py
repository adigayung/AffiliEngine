# File includes\config_loader.py
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config(file_name):
    path = os.path.join(BASE_DIR, "config", file_name)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_app_config():
    return load_config("app.json")


def get_db_config():
    return load_config("database.json")


def get_openrouter_config():
    return load_config("openrouter.json")

def get_upload_tiktok_config():
    return load_config("upload_tiktok.json")