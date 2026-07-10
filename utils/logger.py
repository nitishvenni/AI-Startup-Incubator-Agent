"""
utils/logger.py - Centralised logging configuration.

Call setup_logging() once at app startup (in create_app).
All modules should use:
    import logging
    logger = logging.getLogger(__name__)
"""

import logging
import logging.handlers
import os
import sys


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """Configure root logger with console + rotating file handlers."""
    os.makedirs(log_dir, exist_ok=True)

    level = getattr(logging, log_level.upper(), logging.INFO)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplication on hot-reload
    root.handlers.clear()

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Rotating file handler (5 MB × 3 backups)
    fh = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "incubator.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(level)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # logging.getLogger("werkzeug").setLevel(logging.WARNING)
    # logging.getLogger("ibm_watsonx_ai").setLevel(logging.WARNING)
