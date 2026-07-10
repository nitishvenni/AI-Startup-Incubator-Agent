"""
app.py - Application factory and entry point for the AI Startup Incubator Agent.
"""

import os
import logging
from flask import Flask, request, jsonify
from config import config_by_name
from database.db import init_db, close_db
from utils.logger import setup_logging

logger = logging.getLogger(__name__)
print("[TRACE] MODULE LOAD app.py __file__ =", __file__)


def create_app(config_name: str | None = None) -> Flask:
    """Application factory: create, configure and return the Flask app."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    # Bootstrap logging before anything else
    log_level = "DEBUG" if config_name == "development" else "INFO"
    setup_logging(log_level=log_level)

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    logger.info("Starting AI Startup Incubator Agent [env=%s]", config_name)
    print("[TRACE] ENTER app.create_app(config_name)")
    print("[TRACE] create_app config_name =", repr(config_name))
    print("[TRACE] create_app FLASK_ENV =", repr(os.environ.get("FLASK_ENV")))
    print("[TRACE] create_app IBM_URL env =", repr(os.environ.get("IBM_URL")))
    print("[TRACE] create_app IBM_MODEL config =", repr(app.config.get("IBM_MODEL")))
    print("[TRACE] create_app IBM_URL config =", repr(app.config.get("IBM_URL")))
    print("[TRACE] create_app IBM_PROJECT_ID config =", repr(app.config.get("IBM_PROJECT_ID")))
    print("[TRACE] create_app IBM_API_KEY config length =", len(app.config.get("IBM_API_KEY") or ""))

    @app.before_request
    def trace_browser_request():
        print("[TRACE] Browser -> Flask request")
        print("[TRACE] request.method =", repr(request.method))
        print("[TRACE] request.path =", repr(request.path))
        print("[TRACE] request.full_path =", repr(request.full_path))
        print("[TRACE] request.endpoint =", repr(request.endpoint))
        print("[TRACE] request.view_args =", repr(request.view_args))
        print("[TRACE] request.form =", repr(request.form.to_dict(flat=False)))
        print("[TRACE] request.args =", repr(request.args.to_dict(flat=False)))

    # ------------------------------------------------------------------ #
    # Initialise database schema on startup                                #
    # ------------------------------------------------------------------ #
    with app.app_context():
        init_db(app)

    # ------------------------------------------------------------------ #
    # Security headers                                                     #
    # ------------------------------------------------------------------ #
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # ------------------------------------------------------------------ #
    # Teardown: close DB connection after every request                    #
    # ------------------------------------------------------------------ #
    @app.teardown_appcontext
    def teardown_db(exception=None):
        close_db(app, exception)

    # ------------------------------------------------------------------ #
    # Global error handlers                                                #
    # ------------------------------------------------------------------ #
    @app.errorhandler(404)
    def not_found(e):
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({"error": "Not found"}), 404
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error("Internal server error: %s", e)
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({"error": "Internal server error"}), 500
        from flask import render_template
        return render_template("errors/500.html"), 500

    # ------------------------------------------------------------------ #
    # Register blueprints                                                  #
    # ------------------------------------------------------------------ #
    from routes.main import main_bp
    from routes.startup import startup_bp
    from routes.chat import chat_bp
    from routes.api import api_bp
    from routes.settings import settings_bp
    from routes.mentor import mentor_bp
    from routes.profile import profile_bp
    from routes.analytics import analytics_bp
    from routes.progress import progress_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(startup_bp, url_prefix="/startup")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(mentor_bp, url_prefix="/mentor")
    app.register_blueprint(profile_bp, url_prefix="/profile")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(progress_bp, url_prefix="/progress")

    logger.info("All blueprints registered.")
    print("[TRACE] app.url_map =", app.url_map)
    return app


# ------------------------------------------------------------------ #
# Entry point                                                          #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False,
    )
