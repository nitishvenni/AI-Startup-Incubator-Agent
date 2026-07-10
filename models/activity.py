"""
models/activity.py - Data-access helpers for the activity_log table.
"""

import json
import logging
from database.db import get_db

logger = logging.getLogger(__name__)


def log_activity(app, event_type: str, description: str,
                 project_id: int | None = None, meta: dict | None = None) -> int:
    """
    Insert an activity log entry.

    event_type examples: 'startup_created', 'report_generated',
                         'startup_deleted', 'chat_message', 'export_pdf'
    """
    db = get_db(app)
    meta_json = json.dumps(meta or {})
    cursor = db.execute(
        """
        INSERT INTO activity_log (event_type, description, project_id, meta_json)
        VALUES (?, ?, ?, ?)
        """,
        (event_type, description, project_id, meta_json),
    )
    db.commit()
    logger.debug("Activity logged: [%s] %s", event_type, description)
    return cursor.lastrowid


def get_recent_activity(app, limit: int = 20) -> list:
    """Return the most recent activity entries with optional project names."""
    db = get_db(app)
    rows = db.execute(
        """
        SELECT al.*, sp.startup_name
        FROM activity_log al
        LEFT JOIN startup_projects sp ON al.project_id = sp.id
        ORDER BY al.created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    results = []
    for r in rows:
        item = dict(r)
        try:
            item["meta"] = json.loads(item.get("meta_json", "{}"))
        except (json.JSONDecodeError, TypeError):
            item["meta"] = {}
        results.append(item)
    return results


def get_activity_stats(app) -> dict:
    """Return counts per event_type for the analytics dashboard."""
    db = get_db(app)
    rows = db.execute(
        """
        SELECT event_type, COUNT(*) as count
        FROM activity_log
        GROUP BY event_type
        ORDER BY count DESC
        """
    ).fetchall()
    return {r["event_type"]: r["count"] for r in rows}
