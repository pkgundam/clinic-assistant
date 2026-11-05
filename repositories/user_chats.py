from config.database import conn
from models.user_chat import UserChat


def save(user_id: int, thread_id: str) -> UserChat:
    """Insert the chat row. If this thread already has one, only refresh updated_at and updated_by."""
    row = conn.execute(
        "insert into user_chats (user_id, thread_id, created_by, updated_by) "
        "values (%s, %s, %s, %s) "
        "on conflict (thread_id) where not void_sw "
        "do update set updated_at = now(), updated_by = excluded.updated_by "
        "returning *",
        (user_id, thread_id, user_id, user_id),
    ).fetchone()
    return UserChat(**row)


def find_by_user(user_id: int) -> list[UserChat]:
    """Return this user's chats, most recently updated first."""
    rows = conn.execute(
        "select * from user_chats where user_id = %s and not void_sw order by updated_at desc",
        (user_id,),
    ).fetchall()

    chats = []
    for row in rows:
        chats.append(UserChat(**row))
    return chats


def find_by_thread(user_id: int, thread_id: str) -> UserChat | None:
    """Return the chat with this thread_id, but only if it belongs to this user.

    Someone else's chat gives None, the same as a chat that doesn't exist.
    """
    row = conn.execute(
        "select * from user_chats where user_id = %s and thread_id = %s and not void_sw",
        (user_id, thread_id),
    ).fetchone()
    if row is None:
        return None
    return UserChat(**row)


def save_title(chat_id: int, title: str, user_id: int) -> None:
    """Set the chat's title."""
    conn.execute(
        "update user_chats set title = %s, updated_at = now(), updated_by = %s where id = %s",
        (title, user_id, chat_id),
    )
