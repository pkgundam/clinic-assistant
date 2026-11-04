from config.database import conn
from models.user_fact import UserFact


def get_by_user(user_id: int) -> list[UserFact]:
    """Return all active facts saved for this user, oldest first."""
    rows = conn.execute(
        "select * from user_facts where user_id = %s and not void_sw order by id",
        (user_id,),
    ).fetchall()
    return [UserFact(**row) for row in rows]


def create(user_id: int, fact: str) -> UserFact:
    """Insert a new fact. The logged-in user is the one saving it."""
    row = conn.execute(
        "insert into user_facts (user_id, fact, created_by, updated_by) "
        "values (%s, %s, %s, %s) returning *",
        (user_id, fact, user_id, user_id),
    ).fetchone()
    return UserFact(**row)
