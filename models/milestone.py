"""
models/milestone.py - Data-access helpers for the milestones table.
"""

import logging
from database.db import get_db

logger = logging.getLogger(__name__)

VALID_STATUSES = ("pending", "in_progress", "completed")


def create_milestone(app, project_id: int, title: str,
                     description: str = "", due_date: str | None = None) -> int:
    """Insert a new milestone and return its id."""
    db = get_db(app)
    cursor = db.execute(
        """
        INSERT INTO milestones (project_id, title, description, due_date)
        VALUES (?, ?, ?, ?)
        """,
        (project_id, title.strip(), description.strip(), due_date),
    )
    db.commit()
    return cursor.lastrowid


def get_milestones_by_project(app, project_id: int) -> list:
    """Return all milestones for a project ordered by creation date."""
    db = get_db(app)
    rows = db.execute(
        """
        SELECT * FROM milestones
        WHERE project_id = ?
        ORDER BY created_at ASC
        """,
        (project_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def update_milestone_status(app, milestone_id: int, status: str) -> bool:
    """Update milestone status. Returns True if a row was updated."""
    if status not in VALID_STATUSES:
        logger.warning("Invalid milestone status: %s", status)
        return False
    db = get_db(app)
    db.execute(
        "UPDATE milestones SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (status, milestone_id),
    )
    db.commit()
    return db.execute("SELECT changes()").fetchone()[0] > 0


def delete_milestone(app, milestone_id: int) -> None:
    """Hard-delete a milestone."""
    db = get_db(app)
    db.execute("DELETE FROM milestones WHERE id = ?", (milestone_id,))
    db.commit()


def get_milestone_progress(app, project_id: int) -> dict:
    """Return completion statistics for a project's milestones."""
    milestones = get_milestones_by_project(app, project_id)
    total = len(milestones)
    if total == 0:
        return {"total": 0, "completed": 0, "in_progress": 0, "pending": 0, "pct": 0}
    completed = sum(1 for m in milestones if m["status"] == "completed")
    in_progress = sum(1 for m in milestones if m["status"] == "in_progress")
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "pending": total - completed - in_progress,
        "pct": round(completed / total * 100),
    }
