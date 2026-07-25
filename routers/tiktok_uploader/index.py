# File routers\tiktok_uploader\index.py

from flask import Blueprint, render_template, jsonify, request
import threading

from includes.tiktok_uploader import (
    state,
    uploader_worker
)


tiktok_uploader_bp = Blueprint(
    "tiktok_uploader",
    __name__
)

worker_thread = None


@tiktok_uploader_bp.route("/tiktok_uploader/")
def index():
    return render_template(
        "tiktok_uploader/index.html",
        page_title="tiktok uploader"
    )


@tiktok_uploader_bp.route(
    "/tiktok_uploader/control",
    methods=["POST"]
)
def control():

    global worker_thread

    data = request.json or {}
    status = data.get("status")


    if status == "on":

        if state["status"] == "off":

            state["status"] = "on"

            state["log"].clear()

            worker_thread = threading.Thread(
                target=uploader_worker,
                kwargs={
                    "device": "192.168.100.3:5555", # 192.168.100.3:5555 | FA9TPFWOC6NRG675
                    "username": "@kang.petruk4"
                },
                daemon=True
            )

            worker_thread.start()


    elif status == "off":

        state["status"] = "off"


    return jsonify({
        "success": True,
        "status": state["status"]
    })


@tiktok_uploader_bp.route(
    "/tiktok_uploader/status"
)
def status():

    return jsonify({
        "status": state["status"],
        "log": state["log"][-100:]
    })