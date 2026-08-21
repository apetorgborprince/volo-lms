import os
from pathlib import Path
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

BASE_DIR = Path(__file__).resolve().parent.parent

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    secret = os.getenv("SECRET_KEY")
    if not secret or len(secret) < 32:
        raise RuntimeError("SECRET_KEY must be set and contain at least 32 characters.")

    app.config.from_mapping(
        SECRET_KEY=secret,
        DATABASE=os.getenv("DATABASE_PATH", str(Path(app.instance_path) / "volo_lms.db")),
        UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads")),
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH_MB", "50")) * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "1") == "1",
    )

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    if os.getenv("BEHIND_PROXY", "1") == "1":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

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

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify(ok=False, error="You do not have permission to perform this action."), 403

    @app.errorhandler(404)
    def not_found(error):
        if str(getattr(error, "description", "")).startswith("The requested URL"):
            return jsonify(ok=False, error="Resource not found."), 404
        return error

    return app
