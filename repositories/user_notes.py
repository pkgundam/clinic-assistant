from config.database import conn
from models.user_note import UserNote


def get_by_user(user_id: int) -> list[UserNote]:
    """Return all active notes saved for this user, oldest first."""
    rows = conn.execute(
        "select * from user_notes where user_id = %s and not void_sw order by id",
        (user_id,),
    ).fetchall()
    return [UserNote(**row) for row in rows]


def create(user_id: int, note: str) -> UserNote:
    """Insert a new note. The logged-in user is the one saving it."""
    row = conn.execute(
        "insert into user_notes (user_id, note, created_by, updated_by) "
        "values (%s, %s, %s, %s) returning *",
        (user_id, note, user_id, user_id),
    ).fetchone()
    return UserNote(**row)
