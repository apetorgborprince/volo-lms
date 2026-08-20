import os
from pathlib import Path
from flask import Flask

BASE_DIR = Path(__file__).resolve().parent.parent

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-change-me"),
        DATABASE=str(Path(app.instance_path) / "volo_lms.db"),
        UPLOAD_FOLDER=str(BASE_DIR / "uploads"),
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH_MB", "50")) * 1024 * 1024,
    )
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    from .db import init_app
    init_app(app)

    from .auth import bp as auth_bp
    from .web import bp as web_bp
    from .api import bp as api_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    from .seed import seed_database
    with app.app_context():
        seed_database()

    return app
