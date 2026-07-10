"""
models/incubation_report.py - Data-access helpers for the incubation_reports table.
"""

import json
from database.db import get_db

print("[TRACE] MODULE LOAD models.incubation_report __file__ =", __file__)


def save_incubation_report(app, data: dict) -> int:
    """
    Persist a full incubation report and return its new row id.

    *data* must contain:
        startup_name, founder_name, industry, country, budget,
        target_audience, business_goal, idea_description,
        validation_score, sections  (dict)
    Optional:
        project_id  — foreign key to startup_projects
    """
    print("[TRACE] ENTER models.incubation_report.save_incubation_report(app, data)")
    print("[TRACE] models.incubation_report __file__ =", __file__)
    print("[TRACE] save_incubation_report incoming data keys =", sorted(data.keys()))
    print("[TRACE] save_incubation_report validation_score =", repr(data.get("validation_score")))
    print("[TRACE] save_incubation_report section keys =", sorted((data.get("sections") or {}).keys()))
    db = get_db(app)
    sections_json = json.dumps(data.get("sections", {}), ensure_ascii=False)
    print("[TRACE] save_incubation_report sections_json length =", len(sections_json))
    cursor = db.execute(
        """
        INSERT INTO incubation_reports
            (project_id, startup_name, founder_name, industry, country, budget,
             target_audience, business_goal, idea_description,
             validation_score, sections_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("project_id"),
            data["startup_name"],
            data["founder_name"],
            data["industry"],
            data["country"],
            data["budget"],
            data["target_audience"],
            data["business_goal"],
            data["idea_description"],
            data.get("validation_score", 0),
            sections_json,
        ),
    )
    db.commit()
    print("[TRACE] EXIT save_incubation_report lastrowid =", cursor.lastrowid)
    return cursor.lastrowid


def get_incubation_report_by_id(app, report_id: int) -> dict | None:
    """Return a single incubation report with sections parsed from JSON."""
    print("[TRACE] ENTER models.incubation_report.get_incubation_report_by_id(app, report_id)")
    print("[TRACE] get_incubation_report_by_id report_id =", repr(report_id))
    db = get_db(app)
    row = db.execute(
        "SELECT * FROM incubation_reports WHERE id = ?", (report_id,)
    ).fetchone()
    if not row:
        print("[TRACE] get_incubation_report_by_id result = None")
        return None
    result = dict(row)
    try:
        result["sections"] = json.loads(result.get("sections_json", "{}"))
    except (json.JSONDecodeError, TypeError):
        result["sections"] = {}
    print("[TRACE] get_incubation_report_by_id section keys =", sorted((result.get("sections") or {}).keys()))
    return result


def get_incubation_report_by_project(app, project_id: int) -> dict | None:
    """Return the most recent incubation report for a given startup project."""
    print("[TRACE] ENTER models.incubation_report.get_incubation_report_by_project(app, project_id)")
    print("[TRACE] get_incubation_report_by_project project_id =", repr(project_id))
    db = get_db(app)
    row = db.execute(
        """
        SELECT * FROM incubation_reports
        WHERE project_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (project_id,),
    ).fetchone()
    if not row:
        print("[TRACE] get_incubation_report_by_project result = None")
        return None
    result = dict(row)
    try:
        result["sections"] = json.loads(result.get("sections_json", "{}"))
    except (json.JSONDecodeError, TypeError):
        result["sections"] = {}
    print("[TRACE] get_incubation_report_by_project report id =", repr(result.get("id")))
    print("[TRACE] get_incubation_report_by_project section keys =", sorted((result.get("sections") or {}).keys()))
    return result


def get_all_incubation_reports(app) -> list:
    """Return all incubation reports ordered by most recent first."""
    db = get_db(app)
    rows = db.execute(
        """
        SELECT id, project_id, startup_name, founder_name, industry, country,
               budget, validation_score, created_at
        FROM incubation_reports
        ORDER BY created_at DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def delete_incubation_report(app, report_id: int) -> None:
    """Hard-delete an incubation report by id."""
    db = get_db(app)
    db.execute("DELETE FROM incubation_reports WHERE id = ?", (report_id,))
    db.commit()
