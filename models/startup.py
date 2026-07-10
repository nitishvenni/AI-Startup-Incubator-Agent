"""
models/startup.py - Data-access helpers for the startup_projects table.
"""

from database.db import get_db


def create_startup(app, data: dict) -> int:
    """Insert a new startup project and return its new row id."""
    db = get_db(app)
    cursor = db.execute(
        """
        INSERT INTO startup_projects
            (user_id, startup_name, founder_name, country, industry,
             budget, target_audience, business_goal, idea_description, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """,
        (
            data.get("user_id", 1),
            data["startup_name"],
            data["founder_name"],
            data["country"],
            data["industry"],
            data["budget"],
            data["target_audience"],
            data["business_goal"],
            data["idea_description"],
        ),
    )
    db.commit()
    return cursor.lastrowid


def get_all_startups(app) -> list:
    """Return all startup projects ordered by most recent first."""
    db = get_db(app)
    rows = db.execute(
        "SELECT * FROM startup_projects ORDER BY created_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_startup_by_id(app, project_id: int) -> dict | None:
    """Return a single startup project or None."""
    db = get_db(app)
    row = db.execute(
        "SELECT * FROM startup_projects WHERE id = ?", (project_id,)
    ).fetchone()
    return dict(row) if row else None


def update_startup_status(app, project_id: int, status: str) -> None:
    """Update the status field of a startup project."""
    db = get_db(app)
    db.execute(
        "UPDATE startup_projects SET status = ? WHERE id = ?",
        (status, project_id),
    )
    db.commit()


def delete_startup(app, project_id: int) -> None:
    """Hard-delete a startup project and its related records."""
    db = get_db(app)
    db.execute("DELETE FROM reports WHERE project_id = ?", (project_id,))
    db.execute("DELETE FROM chat_messages WHERE project_id = ?", (project_id,))
    db.execute("DELETE FROM startup_projects WHERE id = ?", (project_id,))
    db.commit()


def get_startup_stats(app) -> dict:
    """Return aggregate counts used by the dashboard."""
    db = get_db(app)
    total = db.execute("SELECT COUNT(*) FROM startup_projects").fetchone()[0]
    analyzed = db.execute(
        "SELECT COUNT(*) FROM startup_projects WHERE status = 'analyzed'"
    ).fetchone()[0]
    pending = db.execute(
        "SELECT COUNT(*) FROM startup_projects WHERE status = 'pending'"
    ).fetchone()[0]
    industries = db.execute(
        """
        SELECT industry, COUNT(*) as count
        FROM startup_projects
        GROUP BY industry
        ORDER BY count DESC
        LIMIT 6
        """
    ).fetchall()
    return {
        "total": total,
        "analyzed": analyzed,
        "pending": pending,
        "industries": [dict(r) for r in industries],
    }
