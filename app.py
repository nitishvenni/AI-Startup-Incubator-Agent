"""
app.py - Application factory and entry point for the AI Startup Incubator Agent.
"""

from flask import Flask
from config import config_by_name
from database.db import init_db, close_db
import os


def create_app(config_name: str | None = None) -> Flask:
    """Application factory: create, configure and return the Flask app."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # ------------------------------------------------------------------ #
    # Initialise database schema on startup                                #
    # ------------------------------------------------------------------ #
    with app.app_context():
        init_db(app)

    # ------------------------------------------------------------------ #
    # Teardown: close DB connection after every request                    #
    # ------------------------------------------------------------------ #
    @app.teardown_appcontext
    def teardown_db(exception=None):
        close_db(app, exception)

    # ------------------------------------------------------------------ #
    # Register blueprints                                                  #
    # ------------------------------------------------------------------ #
    from routes.main import main_bp
    from routes.startup import startup_bp
    from routes.chat import chat_bp
    from routes.api import api_bp
    from routes.settings import settings_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(startup_bp, url_prefix="/startup")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(settings_bp, url_prefix="/settings")

    return app


# ------------------------------------------------------------------ #
# Entry point                                                          #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=flask_app.config["DEBUG"],
    )
