# File : app.py
# ini adala Main/Root file
from flask import Flask, session
from flask_sock import Sock
from includes.config_loader import get_app_config
from includes.websocket import sock
from includes.mysql import get_creator_list, get_creator
import os
import webbrowser
from threading import Timer

config = get_app_config()

app = Flask(__name__)
sock.init_app(app)
# apply config
app.secret_key = config["secret_key"]

# ===============================
# ROUTERS
# ===============================
from routers.dashboard.index import dashboard_bp
from routers.product_rating.index import product_rating_bp
from routers.setting.index import setting_bp
from routers.product_list.index import product_list_bp
from routers.prepare_upload.index import prepare_upload_bp
from routers.analyze_by_phone.index import analyze_by_phone_bp
from routers.tiktok_uploader.index import tiktok_uploader_bp
from routers.product.index import product_ID_bp
from routers.creator.index import creator_bp
from routers.upload_video.index import upload_video_bp
from routers.facebook_uploader.index import facebook_uploader_bp
from routers.production_monitor.index import production_monitor_bp
from routers.video_pipeline.index import video_pipeline_bp
from routers.creator.report import creator_report_bp
from routers.creator.product_exposure import creator_product_exposure_bp
from routers.creator.video_performance import video_performance_bp
from routers.creator.video_analytics import creator_video_analytics_bp
from routers.product_momentum.index import product_momentum_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(product_rating_bp)
app.register_blueprint(setting_bp)
app.register_blueprint(product_list_bp)
app.register_blueprint(prepare_upload_bp)
app.register_blueprint(analyze_by_phone_bp)
app.register_blueprint(tiktok_uploader_bp)
app.register_blueprint(product_ID_bp)
app.register_blueprint(creator_bp)
app.register_blueprint(upload_video_bp)
app.register_blueprint(facebook_uploader_bp)
app.register_blueprint(production_monitor_bp)
app.register_blueprint(video_pipeline_bp)
app.register_blueprint(creator_report_bp)
app.register_blueprint(creator_product_exposure_bp)
app.register_blueprint(video_performance_bp)
app.register_blueprint(creator_video_analytics_bp)
app.register_blueprint(product_momentum_bp)

from routers.websocket.video_uploader import *

@app.context_processor
def inject_creator():

    creators = get_creator_list()

    current_creator = None

    creator_id = session.get("creator_id")

    if creator_id:

        current_creator = get_creator(creator_id)

    return {

        "creators": creators,

        "current_creator": current_creator

    }

def open_browser(URL):
    webbrowser.open(URL)

if __name__ == "__main__":
    url = f"http://127.0.0.1:{config['port']}"

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        Timer(5, open_browser, args=(url,)).start()

    app.run(
        host=config["host"],
        port=config["port"],
        debug=config["debug"]
    )
