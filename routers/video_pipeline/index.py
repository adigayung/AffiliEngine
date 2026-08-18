"""
routes/video_pipeline/index.py — Flask route for the Video Pipeline feature.
"""

import json
import threading
from flask import Blueprint, render_template, request, jsonify
from includes.video_pipeline.processor import create_video

video_pipeline_bp = Blueprint(
    "video_pipeline",
    __name__,
    url_prefix="/video_pipeline",
)


# ================================================================
# In-memory state for the pipeline runner
# ================================================================

def _to_bool(value, default: bool) -> bool:
    """Convert a form value to bool.

    HTML checkbox: "1"/"on"/"true"/"yes" -> True, lainnya -> False.
    Jika value None (field tidak dikirim), gunakan default.
    """
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "on", "yes")


class PipelineRunner:
    """Manages the state of a video pipeline execution."""

    def __init__(self):
        self.running = False
        self.logs: list[str] = []
        self.thread: threading.Thread | None = None

    def add_log(self, text: str):
        """Add a log entry with timestamp and HTML formatting."""
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")

        # Color based on content
        level = "info"
        if "[OK]" in text or "berhasil" in text.lower() or "selesai" in text.lower():
            level = "success"
        elif "[FAIL]" in text or "[ERROR]" in text or "gagal" in text.lower() or "[SKIP]" in text:
            level = "danger"
        elif "[WARN]" in text:
            level = "warning"

        colors = {
            "info": "#4dabf7",
            "success": "#51cf66",
            "warning": "#fcc419",
            "danger": "#ff6b6b",
        }
        icons = {
            "info": "\U0001f5c8\ufe0f",
            "success": "\u2705",
            "warning": "\u26a0\ufe0f",
            "danger": "\u274c",
        }

        color = colors.get(level, "#ffffff")
        icon = icons.get(level, "\u2022")
        text_clean = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        html = (
            f'<div style="line-height:1.25">'
            f'<span style="color:#666">[{now}]</span> '
            f'<span style="color:{color}">{icon}</span> '
            f'<span>{text_clean}</span>'
            f'</div>'
        )
        self.logs.append(html)
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]

    def _run_pipeline(self, root_path: str, preserve_audio: bool, add_music: bool):
        """Run the pipeline in a background thread."""
        try:
            result = create_video(
                root_path,
                log_callback=self.add_log,
                preserve_audio=preserve_audio,
                add_music=add_music,
            )
            self.add_log(f"Pipeline selesai: {result['succeeded']} OK, {result['failed']} FAIL")
        except Exception as e:
            self.add_log(f"[ERROR] Pipeline crash: {e}")
        finally:
            self.running = False

    def start(self, root_path: str, preserve_audio: bool = False, add_music: bool = True) -> bool:
        """Start the pipeline in a background thread."""
        if self.running:
            return False

        self.logs.clear()
        self.running = True
        self.thread = threading.Thread(
            target=self._run_pipeline,
            args=(root_path, preserve_audio, add_music),
            daemon=True,
        )
        self.thread.start()
        return True

    def status(self) -> dict:
        """Return current status as a dict."""
        return {
            "running": self.running,
            "logs": self.logs,
        }


# Singleton instance
pipeline_runner = PipelineRunner()


# ================================================================
# Routes
# ================================================================

@video_pipeline_bp.route("/", methods=["GET"])
def index():
    """Render the Video Pipeline page."""
    return render_template("video_pipeline/index.html")


@video_pipeline_bp.route("/start", methods=["POST"])
def start():
    """Start the video pipeline."""
    root_path = request.form.get("root_path", "").strip()

    # Opsi audio/music (default: preserve_audio=false, add_music=true)
    preserve_audio = _to_bool(request.form.get("preserve_audio"), default=False)
    add_music = _to_bool(request.form.get("add_music"), default=True)

    if not root_path:
        return jsonify({"success": False, "message": "Root path tidak boleh kosong."}), 400

    import os
    if not os.path.isdir(root_path):
        return jsonify({"success": False, "message": "Path tidak ditemukan atau bukan folder."}), 400

    ok = pipeline_runner.start(
        root_path,
        preserve_audio=preserve_audio,
        add_music=add_music,
    )

    if not ok:
        return jsonify({"success": False, "message": "Pipeline sedang berjalan."}), 409

    return jsonify({"success": True, "message": "Pipeline dimulai."})


@video_pipeline_bp.route("/status", methods=["GET"])
def status():
    """Return pipeline status and logs."""
    return jsonify(pipeline_runner.status())
