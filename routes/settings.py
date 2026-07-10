"""
routes/settings.py - Application settings page.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
import os

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET"])
def index():
    """Render the settings page (read-only credential status view)."""
    ibm_api_key    = os.environ.get("IBM_API_KEY", "")
    ibm_project_id = os.environ.get("IBM_PROJECT_ID", "")
    ibm_url        = os.environ.get("IBM_URL", "")
    ibm_model      = os.environ.get("IBM_MODEL", "")

    configured = bool(ibm_api_key and ibm_project_id and ibm_url and ibm_model)

    return render_template(
        "settings.html",
        configured=configured,
        ibm_api_key_set=bool(ibm_api_key),
        ibm_project_id_set=bool(ibm_project_id),
        ibm_url=ibm_url,
        ibm_model=ibm_model,
    )
