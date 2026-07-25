from flask import Blueprint, render_template, request, redirect, jsonify
import json
import os

setting_bp = Blueprint(
    "setting",
    __name__,
    url_prefix="/setting"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =========================
# PAGE
# =========================
@setting_bp.route("/")
def index():
    return render_template(
        "setting/index.html",
        page_title="Settings"
    )

# =========================
# app SETTINGS
# =========================
@setting_bp.route("/app/config", methods=["GET"])
def get_app_config():

    file_path = os.path.join(BASE_DIR, "config", "app.json")

    with open(file_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return jsonify(config)

@setting_bp.route("/app/save", methods=["POST"])
def save_app():

    file_path = os.path.join(BASE_DIR, "config", "app.json")

    with open(file_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    config["app_name"] = request.form.get("app_name")
    config["version"] = request.form.get("version")

    debug_value = request.form.get("debug")
    config["debug"] = True if debug_value == "True" else False

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    return redirect("/setting")

# =========================
# mysql SETTINGS
# =========================

@setting_bp.route("/mysql/config", methods=["GET"])
def get_mysql_config():

    file_path = os.path.join(BASE_DIR, "config", "database.json")

    with open(file_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return jsonify(config)


@setting_bp.route("/mysql/save", methods=["POST"])
def save_mysql():

    file_path = os.path.join(BASE_DIR, "config", "database.json")

    with open(file_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    config["mysql"] = {
        "host": request.form.get("host"),
        "port": request.form.get("port"),
        "user": request.form.get("user"),
        "password": request.form.get("password"),
        "database": request.form.get("database")
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    return redirect("/setting")


# =========================
# AI SETTINGS
# =========================
@setting_bp.route("/ai/save", methods=["POST"])
def save_ai():

    data = {
        "base_url": request.form.get("base_url"),
        "api_key": request.form.get("api_key"),
        "models": {
            "image_analysis": request.form.get("image_model"),
            "text_analysis": request.form.get("text_model")
        }
    }

    file_path = os.path.join(BASE_DIR, "config", "openrouter.json")

    with open(file_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # update only AI section
    config["base_url"] = data["base_url"]
    config["api_key"] = data["api_key"]
    config["models"] = data["models"]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    return redirect("/setting")

@setting_bp.route("/ai/config", methods=["GET"])
def get_ai_config():

    file_path = os.path.join(BASE_DIR, "config", "openrouter.json")

    with open(file_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return jsonify(config)