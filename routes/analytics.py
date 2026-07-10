"""
routes/analytics.py - Analytics Dashboard routes.
"""

import logging
from flask import Blueprint, render_template, current_app
from models.startup import get_startup_stats, get_all_startups
from models.report import get_all_reports
from models.activity import get_activity_stats
from utils.helpers import format_datetime, score_color, score_label

logger = logging.getLogger(__name__)
analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/")
def index():
    """Render the analytics dashboard."""
    app = current_app._get_current_object()
    stats = get_startup_stats(app)
    reports = get_all_reports(app)
    activity_stats = get_activity_stats(app)

    # Score averages
    avg_scores = {"viability": 0, "market": 0, "innovation": 0, "execution": 0}
    score_dist = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
    top_reports = []

    if reports:
        n = len(reports)
        avg_scores = {
            "viability":  round(sum(r["viability_score"]  for r in reports) / n),
            "market":     round(sum(r["market_score"]     for r in reports) / n),
            "innovation": round(sum(r["innovation_score"] for r in reports) / n),
            "execution":  round(sum(r["execution_score"]  for r in reports) / n),
        }
        for r in reports:
            v = r.get("viability_score", 0)
            if v <= 25:
                score_dist["0-25"] += 1
            elif v <= 50:
                score_dist["26-50"] += 1
            elif v <= 75:
                score_dist["51-75"] += 1
            else:
                score_dist["76-100"] += 1

        top_reports = sorted(reports, key=lambda r: r.get("viability_score", 0), reverse=True)[:5]
        for r in top_reports:
            r["viability_color"] = score_color(r["viability_score"])
            r["viability_label"] = score_label(r["viability_score"])
            r["created_at_fmt"] = format_datetime(r["created_at"])

    # Country distribution
    from database.db import get_db
    db = get_db(app)
    countries = [dict(r) for r in db.execute(
        """SELECT country, COUNT(*) as count FROM startup_projects
           GROUP BY country ORDER BY count DESC LIMIT 8"""
    ).fetchall()]

    # Monthly trend (last 6 months)
    monthly = [dict(r) for r in db.execute(
        """SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
           FROM startup_projects
           GROUP BY month ORDER BY month DESC LIMIT 6"""
    ).fetchall()]
    monthly.reverse()

    return render_template(
        "analytics.html",
        stats=stats,
        avg_scores=avg_scores,
        score_dist=score_dist,
        top_reports=top_reports,
        activity_stats=activity_stats,
        countries=countries,
        monthly=monthly,
    )
