"""
utils/validators.py - Input validation helpers.
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 5000
MAX_NAME_LENGTH = 200


def _strip(value: Any) -> str:
    return (value or "").strip()


def validate_startup_form(form) -> tuple[dict, list[str]]:
    """
    Validate and sanitise the startup creation/edit form.

    Returns (cleaned_data dict, list_of_errors).
    """
    data = {
        "startup_name":     _strip(form.get("startup_name")),
        "founder_name":     _strip(form.get("founder_name")),
        "country":          _strip(form.get("country")),
        "industry":         _strip(form.get("industry")),
        "budget":           _strip(form.get("budget")),
        "target_audience":  _strip(form.get("target_audience")),
        "business_goal":    _strip(form.get("business_goal")),
        "idea_description": _strip(form.get("idea_description")),
    }
    errors: list[str] = []

    # Required fields
    required = {
        "startup_name":     "Startup Name",
        "founder_name":     "Founder Name",
        "country":          "Country",
        "industry":         "Industry",
        "budget":           "Budget",
        "target_audience":  "Target Audience",
        "business_goal":    "Business Goal",
        "idea_description": "Idea Description",
    }
    for field, label in required.items():
        if not data[field]:
            errors.append(f"{label} is required.")

    if errors:
        return data, errors

    # Length guards
    for field in ("startup_name", "founder_name"):
        if len(data[field]) > MAX_NAME_LENGTH:
            errors.append(f"{field.replace('_', ' ').title()} is too long (max {MAX_NAME_LENGTH} chars).")

    if len(data["idea_description"]) < 50:
        errors.append("Idea Description must be at least 50 characters.")
    if len(data["idea_description"]) > MAX_TEXT_LENGTH:
        errors.append(f"Idea Description is too long (max {MAX_TEXT_LENGTH} chars).")

    # Basic XSS protection — strip HTML tags from free-text fields
    html_re = re.compile(r"<[^>]+>")
    for field in ("startup_name", "founder_name", "target_audience", "business_goal", "idea_description"):
        if html_re.search(data[field]):
            data[field] = html_re.sub("", data[field])
            logger.warning("HTML stripped from field '%s'", field)

    return data, errors


def validate_profile_form(form) -> tuple[dict, list[str]]:
    """Validate profile settings form."""
    data = {
        "display_name": _strip(form.get("display_name")),
        "email":        _strip(form.get("email")),
        "bio":          _strip(form.get("bio", "")),
    }
    errors: list[str] = []

    if not data["display_name"]:
        errors.append("Display name is required.")
    elif len(data["display_name"]) > MAX_NAME_LENGTH:
        errors.append("Display name is too long.")

    if data["email"] and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", data["email"]):
        errors.append("Invalid email address.")

    if len(data.get("bio", "")) > 500:
        errors.append("Bio must be under 500 characters.")

    return data, errors
