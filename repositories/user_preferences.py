from config.database import conn
from models.user_preference import UserPreference


def get_by_user(user_id: int) -> list[UserPreference]:
    """Return all active preferences saved for this user, oldest first."""
    rows = conn.execute(
        "select * from user_preferences where user_id = %s and not void_sw order by id",
        (user_id,),
    ).fetchall()
    return [UserPreference(**row) for row in rows]


def create(user_id: int, preference: str) -> UserPreference:
    """Insert a new preference. The logged-in user is the one saving it."""
    row = conn.execute(
        "insert into user_preferences (user_id, preference, created_by, updated_by) "
        "values (%s, %s, %s, %s) returning *",
        (user_id, preference, user_id, user_id),
    ).fetchone()
    return UserPreference(**row)
