"""
utils/helpers.py - General-purpose helper utilities.
"""

import re
from datetime import datetime


def slugify(text: str) -> str:
    """Convert a string to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def format_datetime(dt_string: str, fmt: str = "%b %d, %Y %I:%M %p") -> str:
    """Parse an SQLite datetime string and return a human-readable format."""
    try:
        dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
        return dt.strftime(fmt)
    except (ValueError, TypeError):
        return dt_string or "—"


def score_label(score: int) -> str:
    """Return a qualitative label for a numeric score (0–100)."""
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 50:
        return "Fair"
    return "Needs Work"


def score_color(score: int) -> str:
    """Return a Bootstrap colour class name matching the score range."""
    if score >= 80:
        return "success"
    if score >= 65:
        return "info"
    if score >= 50:
        return "warning"
    return "danger"


def truncate(text: str, max_len: int = 120) -> str:
    """Truncate a string to *max_len* characters and append ellipsis if needed."""
    if not text:
        return ""
    return text if len(text) <= max_len else text[:max_len].rstrip() + "…"


INDUSTRY_ICONS: dict[str, str] = {
    "Technology": "bi-cpu",
    "Healthcare": "bi-heart-pulse",
    "Finance": "bi-cash-coin",
    "Education": "bi-mortarboard",
    "E-commerce": "bi-cart3",
    "Real Estate": "bi-building",
    "Food & Beverage": "bi-cup-hot",
    "Transportation": "bi-truck",
    "Entertainment": "bi-film",
    "Agriculture": "bi-tree",
    "Energy": "bi-lightning-charge",
    "Fashion": "bi-handbag",
    "Travel": "bi-airplane",
    "Sports": "bi-trophy",
    "Other": "bi-grid",
}


def industry_icon(industry: str) -> str:
    """Return the Bootstrap Icons class for an industry string."""
    return INDUSTRY_ICONS.get(industry, "bi-grid")
