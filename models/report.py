"""
models/report.py - Data-access helpers for the reports table.
"""

from database.db import get_db


def create_report(app, data: dict) -> int:
    """Insert an AI-generated report and return its row id."""
    db = get_db(app)
    cursor = db.execute(
        """
        INSERT INTO reports
            (project_id, report_type, content,
             viability_score, market_score, innovation_score, execution_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["project_id"],
            data.get("report_type", "full_analysis"),
            data["content"],
            data.get("viability_score", 0),
            data.get("market_score", 0),
            data.get("innovation_score", 0),
            data.get("execution_score", 0),
        ),
    )
    db.commit()
    return cursor.lastrowid


def get_report_by_project(app, project_id: int) -> dict | None:
    """Return the most recent report for a given project."""
    db = get_db(app)
    row = db.execute(
        """
        SELECT * FROM reports
        WHERE project_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (project_id,),
    ).fetchone()
    return dict(row) if row else None


def get_all_reports(app) -> list:
    """Return all reports joined with their project names."""
    db = get_db(app)
    rows = db.execute(
        """
        SELECT r.*, sp.startup_name, sp.industry
        FROM reports r
        JOIN startup_projects sp ON r.project_id = sp.id
        ORDER BY r.created_at DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]
