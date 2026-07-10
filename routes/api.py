"""
routes/api.py - JSON API endpoints (AJAX calls from the frontend).
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from models.chat import save_message, get_messages_by_project
from models.startup import get_startup_by_id, get_all_startups, get_startup_stats, search_startups
from models.activity import get_recent_activity, get_activity_stats
from models.milestone import (
    create_milestone, get_milestones_by_project,
    update_milestone_status, delete_milestone,
)
from services.watsonx_service import chat_with_mentor

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)


# ------------------------------------------------------------------ #
# Chat                                                                 #
# ------------------------------------------------------------------ #

@api_bp.route("/chat/send", methods=["POST"])
def chat_send():
    """
    Receive a user message, call Granite, persist both turns, return JSON.
    Expected JSON body: { "message": "...", "project_id": <int|null> }
    """
    payload = request.get_json(silent=True) or {}
    user_message = (payload.get("message") or "").strip()
    project_id = payload.get("project_id")

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400
    if len(user_message) > 4000:
        return jsonify({"error": "Message is too long (max 4000 characters)."}), 400

    app = current_app._get_current_object()
    context: dict = {}

    if project_id:
        try:
            project_id = int(project_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid project_id."}), 400
        startup = get_startup_by_id(app, project_id)
        if startup:
            context["startup_name"] = startup["startup_name"]
            context["industry"] = startup["industry"]
        history = get_messages_by_project(app, project_id)
        context["history"] = history

    save_message(app, project_id, "user", user_message)

    try:
        ai_reply = chat_with_mentor(app, user_message, context)
    except RuntimeError as exc:
        logger.error("Chat generation failed: %s", exc)
        return jsonify({"error": str(exc)}), 503

    save_message(app, project_id, "assistant", ai_reply)
    return jsonify({"reply": ai_reply})


# ------------------------------------------------------------------ #
# Dashboard / Analytics stats                                          #
# ------------------------------------------------------------------ #

@api_bp.route("/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """Return aggregate stats as JSON (used by Chart.js on the dashboard)."""
    app = current_app._get_current_object()
    stats = get_startup_stats(app)
    return jsonify(stats)


@api_bp.route("/analytics/data", methods=["GET"])
def analytics_data():
    """Return extended analytics data for the analytics dashboard."""
    from models.report import get_all_reports
    app = current_app._get_current_object()
    stats = get_startup_stats(app)
    reports = get_all_reports(app)
    activity_stats = get_activity_stats(app)

    # Score distribution buckets
    buckets = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
    avg_scores = {"viability": 0, "market": 0, "innovation": 0, "execution": 0}
    if reports:
        for r in reports:
            v = r.get("viability_score", 0)
            if v <= 25:
                buckets["0-25"] += 1
            elif v <= 50:
                buckets["26-50"] += 1
            elif v <= 75:
                buckets["51-75"] += 1
            else:
                buckets["76-100"] += 1
        n = len(reports)
        avg_scores = {
            "viability":  round(sum(r["viability_score"]  for r in reports) / n),
            "market":     round(sum(r["market_score"]     for r in reports) / n),
            "innovation": round(sum(r["innovation_score"] for r in reports) / n),
            "execution":  round(sum(r["execution_score"]  for r in reports) / n),
        }

    # Country distribution
    from database.db import get_db
    db = get_db(app)
    countries = db.execute(
        """SELECT country, COUNT(*) as count FROM startup_projects
           GROUP BY country ORDER BY count DESC LIMIT 8"""
    ).fetchall()

    # Monthly trend (last 6 months)
    monthly = db.execute(
        """SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
           FROM startup_projects
           GROUP BY month ORDER BY month DESC LIMIT 6"""
    ).fetchall()

    return jsonify({
        "stats": stats,
        "score_distribution": buckets,
        "avg_scores": avg_scores,
        "activity_stats": activity_stats,
        "countries": [dict(r) for r in countries],
        "monthly_trend": [dict(r) for r in reversed(list(monthly))],
    })


# ------------------------------------------------------------------ #
# Search                                                               #
# ------------------------------------------------------------------ #

@api_bp.route("/search", methods=["GET"])
def search():
    """Quick search across startups — returns JSON."""
    app = current_app._get_current_object()
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"results": []})
    if len(q) > 200:
        return jsonify({"error": "Query too long."}), 400

    results = search_startups(app, q=q)[:10]
    return jsonify({
        "results": [
            {
                "id":           r["id"],
                "startup_name": r["startup_name"],
                "industry":     r["industry"],
                "country":      r["country"],
                "status":       r["status"],
            }
            for r in results
        ]
    })


# ------------------------------------------------------------------ #
# Milestones                                                           #
# ------------------------------------------------------------------ #

@api_bp.route("/milestones", methods=["POST"])
def add_milestone():
    """Create a new milestone for a project."""
    payload = request.get_json(silent=True) or {}
    project_id = payload.get("project_id")
    title = (payload.get("title") or "").strip()

    if not project_id or not title:
        return jsonify({"error": "project_id and title are required."}), 400
    if len(title) > 200:
        return jsonify({"error": "Title too long."}), 400

    app = current_app._get_current_object()
    mid = create_milestone(
        app, int(project_id), title,
        description=payload.get("description", ""),
        due_date=payload.get("due_date"),
    )
    return jsonify({"id": mid, "title": title, "status": "pending"}), 201


@api_bp.route("/milestones/<int:milestone_id>/status", methods=["PATCH"])
def update_milestone(milestone_id: int):
    """Update the status of a milestone."""
    payload = request.get_json(silent=True) or {}
    status = (payload.get("status") or "").strip()
    if not status:
        return jsonify({"error": "status is required."}), 400

    app = current_app._get_current_object()
    ok = update_milestone_status(app, milestone_id, status)
    if not ok:
        return jsonify({"error": "Invalid status or milestone not found."}), 400
    return jsonify({"ok": True})


@api_bp.route("/milestones/<int:milestone_id>", methods=["DELETE"])
def remove_milestone(milestone_id: int):
    """Delete a milestone."""
    app = current_app._get_current_object()
    delete_milestone(app, milestone_id)
    return jsonify({"ok": True})


# ------------------------------------------------------------------ #
# Recent Activity                                                      #
# ------------------------------------------------------------------ #

@api_bp.route("/activity", methods=["GET"])
def recent_activity():
    """Return recent activity as JSON."""
    app = current_app._get_current_object()
    limit = min(int(request.args.get("limit", 10)), 50)
    items = get_recent_activity(app, limit=limit)
    from utils.helpers import format_datetime
    for item in items:
        item["created_at_fmt"] = format_datetime(item["created_at"])
    return jsonify({"activity": items})
