"""
models/chat.py - Data-access helpers for the chat_messages table.
"""

from database.db import get_db


def save_message(app, project_id: int | None, role: str, content: str) -> int:
    """Persist a chat message and return its row id."""
    db = get_db(app)
    cursor = db.execute(
        "INSERT INTO chat_messages (project_id, role, content) VALUES (?, ?, ?)",
        (project_id, role, content),
    )
    db.commit()
    return cursor.lastrowid


def get_messages_by_project(app, project_id: int) -> list:
    """Return the full conversation history for a project."""
    db = get_db(app)
    rows = db.execute(
        """
        SELECT * FROM chat_messages
        WHERE project_id = ?
        ORDER BY created_at ASC
        """,
        (project_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_recent_messages(app, limit: int = 20) -> list:
    """Return the most recent chat messages across all projects."""
    db = get_db(app)
    rows = db.execute(
        """
        SELECT cm.*, sp.startup_name
        FROM chat_messages cm
        LEFT JOIN startup_projects sp ON cm.project_id = sp.id
        ORDER BY cm.created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def clear_project_chat(app, project_id: int) -> None:
    """Remove all chat messages for a given project."""
    db = get_db(app)
    db.execute("DELETE FROM chat_messages WHERE project_id = ?", (project_id,))
    db.commit()
