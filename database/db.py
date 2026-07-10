"""
database/db.py - Low-level SQLite connection helper.

Provides get_db() for request-scoped connections and
init_db() for first-time schema creation.
"""

import sqlite3
import os
from flask import g


def get_db(app):
    """Return (or create) the per-request SQLite connection stored on Flask's 'g'."""
    if "db" not in g:
        db_path = app.config["DATABASE_PATH"]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrent read performance.
        g.db.execute("PRAGMA journal_mode=WAL;")
    return g.db


def close_db(app, e=None):
    """Tear down the per-request database connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create all tables if they do not exist yet."""
    db_path = app.config["DATABASE_PATH"]
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    # ------------------------------------------------------------------ #
    # Users table                                                          #
    # ------------------------------------------------------------------ #
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
        """
    )

    # ------------------------------------------------------------------ #
    # StartupProjects table                                                #
    # ------------------------------------------------------------------ #
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS startup_projects (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL DEFAULT 1,
            startup_name     TEXT    NOT NULL,
            founder_name     TEXT    NOT NULL,
            country          TEXT    NOT NULL,
            industry         TEXT    NOT NULL,
            budget           TEXT    NOT NULL,
            target_audience  TEXT    NOT NULL,
            business_goal    TEXT    NOT NULL,
            idea_description TEXT    NOT NULL,
            status           TEXT    NOT NULL DEFAULT 'pending',
            created_at       TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )

    # ------------------------------------------------------------------ #
    # Reports table                                                        #
    # ------------------------------------------------------------------ #
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id      INTEGER NOT NULL,
            report_type     TEXT    NOT NULL DEFAULT 'full_analysis',
            content         TEXT    NOT NULL,
            viability_score INTEGER DEFAULT 0,
            market_score    INTEGER DEFAULT 0,
            innovation_score INTEGER DEFAULT 0,
            execution_score INTEGER DEFAULT 0,
            created_at      TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES startup_projects(id)
        );
        """
    )

    # ------------------------------------------------------------------ #
    # Chat messages table                                                  #
    # ------------------------------------------------------------------ #
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id  INTEGER,
            role        TEXT NOT NULL CHECK(role IN ('user','assistant')),
            content     TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES startup_projects(id)
        );
        """
    )

    conn.commit()
    conn.close()
