"""
routes/main.py - Landing page and Dashboard routes.
"""

from flask import Blueprint, render_template, current_app
from models.startup import get_all_startups, get_startup_stats
from models.report import get_all_reports
from utils.helpers import format_datetime, score_label, score_color, industry_icon

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def landing():
    """Public landing page."""
    return render_template("landing.html")


@main_bp.route("/dashboard")
def dashboard():
    """Main dashboard with aggregate statistics and recent activity."""
    app = current_app._get_current_object()
    stats = get_startup_stats(app)
    recent_startups = get_all_startups(app)[:5]
    recent_reports = get_all_reports(app)[:5]

    # Enrich with display helpers
    for s in recent_startups:
        s["icon"] = industry_icon(s["industry"])
        s["created_at_fmt"] = format_datetime(s["created_at"])

    for r in recent_reports:
        r["viability_label"] = score_label(r["viability_score"])
        r["viability_color"] = score_color(r["viability_score"])
        r["created_at_fmt"] = format_datetime(r["created_at"])

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_startups=recent_startups,
        recent_reports=recent_reports,
    )


@main_bp.route("/history")
def history():
    """Project history page — all past startup analyses."""
    app = current_app._get_current_object()
    startups = get_all_startups(app)
    reports_map: dict[int, dict] = {}
    for r in get_all_reports(app):
        pid = r["project_id"]
        if pid not in reports_map:
            reports_map[pid] = r

    enriched = []
    for s in startups:
        report = reports_map.get(s["id"])
        enriched.append(
            {
                **s,
                "icon": industry_icon(s["industry"]),
                "created_at_fmt": format_datetime(s["created_at"]),
                "report": report,
                "viability_label": score_label(report["viability_score"]) if report else "—",
                "viability_color": score_color(report["viability_score"]) if report else "secondary",
            }
        )

    return render_template("history.html", startups=enriched)
