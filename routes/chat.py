"""
routes/chat.py - AI Chat Assistant routes.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    current_app,
)
from models.startup import get_all_startups, get_startup_by_id
from models.chat import save_message, get_messages_by_project

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/", methods=["GET"])
def index():
    """Chat assistant landing – optionally pre-loads a project context."""
    app = current_app._get_current_object()
    project_id = request.args.get("project_id", type=int)
    all_startups = get_all_startups(app)
    selected_startup = None
    messages = []

    if project_id:
        selected_startup = get_startup_by_id(app, project_id)
        messages = get_messages_by_project(app, project_id)

    return render_template(
        "chat.html",
        all_startups=all_startups,
        selected_startup=selected_startup,
        messages=messages,
        project_id=project_id,
    )
