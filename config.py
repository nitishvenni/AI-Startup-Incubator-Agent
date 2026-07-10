"""
config.py - Centralised application configuration.

All sensitive values are loaded exclusively from environment variables
(populated via .env at startup). Nothing is hardcoded.
"""

import os
from dotenv import load_dotenv

# Load .env into the process environment before anything else reads it.
load_dotenv(override=True)

print("=" * 50)
print("ENV Loaded")
print("IBM_API_KEY:", os.getenv("IBM_API_KEY")[:12] if os.getenv("IBM_API_KEY") else "NOT FOUND")
print("IBM_PROJECT_ID:", os.getenv("IBM_PROJECT_ID"))
print("IBM_URL:", os.getenv("IBM_URL"))
print("=" * 50)


class Config:
    # ------------------------------------------------------------------ #
    # Flask core                                                           #
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = os.environ.get("FLASK_SECRET_KEY", "change-me-in-production")
    ENV: str = os.environ.get("FLASK_ENV", "production")
    DEBUG: bool = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    # ------------------------------------------------------------------ #
    # Database                                                             #
    # ------------------------------------------------------------------ #
    DATABASE_PATH: str = os.environ.get("DATABASE_PATH", "database/incubator.db")

    # ------------------------------------------------------------------ #
    # IBM watsonx.ai                                                       #
    # ------------------------------------------------------------------ #
    IBM_API_KEY: str = os.environ.get("IBM_API_KEY", "")
    IBM_PROJECT_ID: str = os.environ.get("IBM_PROJECT_ID", "")
    IBM_URL: str = os.environ.get("IBM_URL", "https://us-south.ml.cloud.ibm.com")
    IBM_MODEL: str = os.environ.get("IBM_MODEL", "ibm/granite-13b-instruct-v2")

    # ------------------------------------------------------------------ #
    # watsonx generation parameters (sensible defaults)                   #
    # ------------------------------------------------------------------ #
    WX_MAX_NEW_TOKENS = 1024
    WX_MIN_NEW_TOKENS = 1
    WX_TEMPERATURE = 0.3
    WX_TOP_P = 1.0
    WX_TOP_K = 0
    WX_REPETITION_PENALTY = 1.0

    # ------------------------------------------------------------------ #
    # Mentor incubation report parameters (richer output needs more tokens)#
    # ------------------------------------------------------------------ #
    MENTOR_MAX_NEW_TOKENS: int = 4096
    MENTOR_TEMPERATURE: float = 0.75


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"


class ProductionConfig(Config):
    DEBUG = False
    ENV = "production"


# Map string name → class so app factory can select the right config.
config_by_name: dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

