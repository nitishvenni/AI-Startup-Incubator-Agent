"""
database/db.py - Low-level SQLite connection helper.

Provides get_db() for request-scoped connections and
init_db() for first-time schema creation.
"""

import sqlite3
import os
from flask import g
import logging

logger = logging.getLogger(__name__)


def get_db(app):
    """Return (or create) the per-request SQLite connection stored on Flask's 'g'."""
    if "db" not in g:
        db_path = app.config["DATABASE_PATH"]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrent read performance.
        g.db.execute("PRAGMA journal_mode=WAL;")
        g.db.execute("PRAGMA foreign_keys=ON;")
    return g.db


def close_db(app, e=None):
    """Tear down the per-request database connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create all tables if they do not exist yet (additive migrations only)."""
    db_path = app.config["DATABASE_PATH"]
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
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

    # ----------------------------------------------------------
    # Create a default guest user if one doesn't exist
    # ----------------------------------------------------------
    cursor.execute("""
    INSERT OR IGNORE INTO users (id, name, email, password)
    VALUES (
        1,
        'Guest User',
        'guest@example.com',
        'guest_password'
    )
    """)
    # ------------------------------------------------------------------ #
    # User Profile table (extended settings per user)                     #
    # ------------------------------------------------------------------ #
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL DEFAULT 1,
            display_name TEXT    NOT NULL DEFAULT 'Founder',
            email        TEXT    NOT NULL DEFAULT '',
            bio          TEXT    DEFAULT '',
            avatar_color TEXT    DEFAULT '#3b82d4',
            created_at   TEXT    DEFAULT (datetime('now')),
            updated_at   TEXT    DEFAULT (datetime('now'))
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
            stage            TEXT    NOT NULL DEFAULT 'idea',
            created_at       TEXT    DEFAULT (datetime('now')),
            updated_at       TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )

    # Additive columns for existing databases
    _add_column_if_missing(cursor, "startup_projects", "stage", "TEXT NOT NULL DEFAULT 'idea'")
    _add_column_if_missing(cursor, "startup_projects", "updated_at", "TEXT DEFAULT (datetime('now'))")

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

    # ------------------------------------------------------------------ #
    # Incubation Reports table                                             #
    # ------------------------------------------------------------------ #
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS incubation_reports (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id           INTEGER DEFAULT NULL,
            startup_name         TEXT    NOT NULL,
            founder_name         TEXT    NOT NULL,
            industry             TEXT    NOT NULL,
            country              TEXT    NOT NULL,
            budget               TEXT    NOT NULL,
            target_audience      TEXT    NOT NULL,
            business_goal        TEXT    NOT NULL,
            idea_description     TEXT    NOT NULL,
            validation_score     INTEGER DEFAULT 0,
            sections_json        TEXT    NOT NULL DEFAULT '{}',
            created_at           TEXT    DEFAULT (datetime('now'))
        );
        """
    )
    # Additive migration: add project_id to existing databases
    _add_column_if_missing(cursor, "incubation_reports", "project_id", "INTEGER DEFAULT NULL")

    # ------------------------------------------------------------------ #
    # Activity Log table                                                   #
    # ------------------------------------------------------------------ #
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type  TEXT    NOT NULL,
            description TEXT    NOT NULL,
            project_id  INTEGER,
            meta_json   TEXT    DEFAULT '{}',
            created_at  TEXT    DEFAULT (datetime('now'))
        );
        """
    )

    # ------------------------------------------------------------------ #
    # Milestones table (Startup Progress Tracker)                         #
    # ------------------------------------------------------------------ #
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS milestones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id  INTEGER NOT NULL,
            title       TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            status      TEXT    NOT NULL DEFAULT 'pending'
                        CHECK(status IN ('pending','in_progress','completed')),
            due_date    TEXT    DEFAULT NULL,
            created_at  TEXT    DEFAULT (datetime('now')),
            updated_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES startup_projects(id)
        );
        """
    )

    conn.commit()
    conn.close()
    logger.info("Database schema initialised/verified.")


def _add_column_if_missing(cursor, table: str, column: str, definition: str) -> None:
    """Add a column to an existing table only if it doesn't exist yet."""
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition};")
    except Exception:
        pass  # Column already exists — that's fine
