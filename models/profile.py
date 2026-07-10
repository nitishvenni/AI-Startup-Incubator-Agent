"""
models/profile.py - Data-access helpers for the user_profiles table.
"""

import logging
from database.db import get_db

logger = logging.getLogger(__name__)

_DEFAULT_PROFILE = {
    "id": 1,
    "user_id": 1,
    "display_name": "Founder",
    "email": "",
    "bio": "",
    "avatar_color": "#3b82d4",
}


def get_profile(app, user_id: int = 1) -> dict:
    """Return the profile for user_id, creating a default if none exists."""
    db = get_db(app)
    row = db.execute(
        "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row:
        return dict(row)
    # Auto-create default profile
    db.execute(
        """
        INSERT INTO user_profiles (user_id, display_name, email, bio, avatar_color)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, "Founder", "", "", "#3b82d4"),
    )
    db.commit()
    return dict(_DEFAULT_PROFILE)


def update_profile(app, user_id: int, data: dict) -> None:
    """Upsert a user profile."""
    db = get_db(app)
    existing = db.execute(
        "SELECT id FROM user_profiles WHERE user_id = ?", (user_id,)
    ).fetchone()
    if existing:
        db.execute(
            """
            UPDATE user_profiles
            SET display_name = ?, email = ?, bio = ?,
                avatar_color = ?, updated_at = datetime('now')
            WHERE user_id = ?
            """,
            (
                data.get("display_name", "Founder"),
                data.get("email", ""),
                data.get("bio", ""),
                data.get("avatar_color", "#3b82d4"),
                user_id,
            ),
        )
    else:
        db.execute(
            """
            INSERT INTO user_profiles (user_id, display_name, email, bio, avatar_color)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                data.get("display_name", "Founder"),
                data.get("email", ""),
                data.get("bio", ""),
                data.get("avatar_color", "#3b82d4"),
            ),
        )
    db.commit()
    logger.info("Profile updated for user_id=%s", user_id)
