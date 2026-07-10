"""
routes/api.py - JSON API endpoints (AJAX calls from the frontend).
"""

from flask import Blueprint, request, jsonify, current_app
from models.chat import save_message, get_messages_by_project
from models.startup import get_startup_by_id
from services.watsonx_service import chat_with_mentor

api_bp = Blueprint("api", __name__)


@api_bp.route("/chat/send", methods=["POST"])
def chat_send():
    """
    Receive a user message, call Granite, persist both turns, return JSON.

    Expected JSON body:
        { "message": "...", "project_id": <int|null> }
    """
    payload = request.get_json(silent=True) or {}
    user_message = (payload.get("message") or "").strip()
    project_id = payload.get("project_id")  # may be None

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    app = current_app._get_current_object()

    # Build conversation context
    context: dict = {}
    if project_id:
        startup = get_startup_by_id(app, project_id)
        if startup:
            context["startup_name"] = startup["startup_name"]
            context["industry"] = startup["industry"]
        history = get_messages_by_project(app, project_id)
        context["history"] = history

    # Persist user message
    save_message(app, project_id, "user", user_message)

    # Call Granite
    try:
        ai_reply = chat_with_mentor(app, user_message, context)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    # Persist assistant reply
    save_message(app, project_id, "assistant", ai_reply)

    return jsonify({"reply": ai_reply})


@api_bp.route("/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """Return aggregate stats as JSON (used by Chart.js on the dashboard)."""
    from models.startup import get_startup_stats

    app = current_app._get_current_object()
    stats = get_startup_stats(app)
    return jsonify(stats)
