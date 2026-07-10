"""
routes/main.py - Landing page, Dashboard, History routes.
"""

import logging
from flask import Blueprint, render_template, current_app, request
from models.startup import get_all_startups, get_startup_stats, search_startups
from models.report import get_all_reports
from models.activity import get_recent_activity
from models.profile import get_profile
from utils.helpers import format_datetime, score_label, score_color, industry_icon

logger = logging.getLogger(__name__)
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
    recent_startups = get_all_startups(app)[:6]
    recent_reports = get_all_reports(app)[:5]
    activity = get_recent_activity(app, limit=8)
    profile = get_profile(app)

    for s in recent_startups:
        s["icon"] = industry_icon(s["industry"])
        s["created_at_fmt"] = format_datetime(s["created_at"])

    for r in recent_reports:
        r["viability_label"] = score_label(r["viability_score"])
        r["viability_color"] = score_color(r["viability_score"])
        r["created_at_fmt"] = format_datetime(r["created_at"])

    for a in activity:
        a["created_at_fmt"] = format_datetime(a["created_at"])

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_startups=recent_startups,
        recent_reports=recent_reports,
        activity=activity,
        profile=profile,
    )


@main_bp.route("/history")
def history():
    """Project history page — all past startup analyses with search."""
    app = current_app._get_current_object()
    q = request.args.get("q", "").strip()
    industry_filter = request.args.get("industry", "").strip()
    status_filter = request.args.get("status", "").strip()

    startups = search_startups(app, q=q, industry=industry_filter, status=status_filter)
    reports_map: dict[int, dict] = {}
    for r in get_all_reports(app):
        pid = r["project_id"]
        if pid not in reports_map:
            reports_map[pid] = r

    enriched = []
    for s in startups:
        report = reports_map.get(s["id"])
        enriched.append({
            **s,
            "icon": industry_icon(s["industry"]),
            "created_at_fmt": format_datetime(s["created_at"]),
            "report": report,
            "viability_label": score_label(report["viability_score"]) if report else "—",
            "viability_color": score_color(report["viability_score"]) if report else "secondary",
        })

    from utils.constants import INDUSTRIES
    return render_template(
        "history.html",
        startups=enriched,
        q=q,
        industry_filter=industry_filter,
        status_filter=status_filter,
        industries=INDUSTRIES,
    )


@main_bp.route("/activity")
def activity():
    """Recent activity log page."""
    app = current_app._get_current_object()
    items = get_recent_activity(app, limit=50)
    for a in items:
        a["created_at_fmt"] = format_datetime(a["created_at"])
    return render_template("activity.html", activity=items)
