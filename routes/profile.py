"""
routes/profile.py - Profile Settings routes.
"""

import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from models.profile import get_profile, update_profile
from models.activity import log_activity
from utils.validators import validate_profile_form

logger = logging.getLogger(__name__)
profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/", methods=["GET"])
def index():
    """Display the user profile settings page."""
    app = current_app._get_current_object()
    profile = get_profile(app)
    return render_template("profile.html", profile=profile)


@profile_bp.route("/update", methods=["POST"])
def update():
    """Save profile settings."""
    app = current_app._get_current_object()
    data, errors = validate_profile_form(request.form)
    if errors:
        for err in errors:
            flash(err, "danger")
        return redirect(url_for("profile.index"))

    data["avatar_color"] = request.form.get("avatar_color", "#3b82d4").strip() or "#3b82d4"
    update_profile(app, user_id=1, data=data)
    log_activity(app, "profile_updated", "Profile settings updated.")
    flash("Profile updated successfully!", "success")
    return redirect(url_for("profile.index"))
