"""
routes/progress.py - Startup Progress Tracker routes.
"""

import logging
from flask import (
    Blueprint, render_template, request, flash,
    redirect, url_for, current_app, jsonify,
)
from models.startup import get_startup_by_id, get_all_startups
from models.milestone import (
    create_milestone, get_milestones_by_project,
    update_milestone_status, delete_milestone, get_milestone_progress,
)
from models.activity import log_activity
from utils.helpers import format_datetime, industry_icon

logger = logging.getLogger(__name__)
progress_bp = Blueprint("progress", __name__)


@progress_bp.route("/")
def index():
    """List all startups with their progress overview."""
    app = current_app._get_current_object()
    startups = get_all_startups(app)
    for s in startups:
        s["icon"] = industry_icon(s["industry"])
        s["created_at_fmt"] = format_datetime(s["created_at"])
        s["progress"] = get_milestone_progress(app, s["id"])
    return render_template("progress_index.html", startups=startups)


@progress_bp.route("/<int:project_id>", methods=["GET"])
def detail(project_id: int):
    """Show milestone tracker for a specific startup."""
    app = current_app._get_current_object()
    startup = get_startup_by_id(app, project_id)
    if not startup:
        flash("Startup not found.", "danger")
        return redirect(url_for("progress.index"))

    startup["icon"] = industry_icon(startup["industry"])
    startup["created_at_fmt"] = format_datetime(startup["created_at"])

    milestones = get_milestones_by_project(app, project_id)
    for m in milestones:
        m["created_at_fmt"] = format_datetime(m["created_at"])

    progress = get_milestone_progress(app, project_id)
    return render_template(
        "progress_detail.html",
        startup=startup,
        milestones=milestones,
        progress=progress,
    )


@progress_bp.route("/<int:project_id>/add", methods=["POST"])
def add(project_id: int):
    """Add a milestone to a startup."""
    app = current_app._get_current_object()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "").strip() or None

    if not title:
        flash("Milestone title is required.", "danger")
    elif len(title) > 200:
        flash("Milestone title is too long.", "danger")
    else:
        create_milestone(app, project_id, title, description, due_date)
        log_activity(app, "milestone_added", f"Milestone '{title}' added.", project_id=project_id)
        flash(f"Milestone '{title}' added!", "success")

    return redirect(url_for("progress.detail", project_id=project_id))


@progress_bp.route("/milestone/<int:milestone_id>/status", methods=["POST"])
def set_status(milestone_id: int):
    """Update a milestone status (from form POST)."""
    app = current_app._get_current_object()
    status = request.form.get("status", "").strip()
    project_id = request.form.get("project_id", type=int)

    ok = update_milestone_status(app, milestone_id, status)
    if not ok:
        flash("Invalid status.", "danger")
    else:
        flash("Milestone updated.", "success")

    if project_id:
        return redirect(url_for("progress.detail", project_id=project_id))
    return redirect(url_for("progress.index"))


@progress_bp.route("/milestone/<int:milestone_id>/delete", methods=["POST"])
def remove(milestone_id: int):
    """Delete a milestone."""
    app = current_app._get_current_object()
    project_id = request.form.get("project_id", type=int)
    delete_milestone(app, milestone_id)
    flash("Milestone removed.", "info")
    if project_id:
        return redirect(url_for("progress.detail", project_id=project_id))
    return redirect(url_for("progress.index"))
