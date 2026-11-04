from config.database import conn
from models.user_visit import UserVisit


def get_by_user(user_id: int) -> list[UserVisit]:
    """Return all of this user's visits, most recently updated first."""
    rows = conn.execute(
        "select * from user_visits where user_id = %s and not void_sw order by updated_at desc",
        (user_id,),
    ).fetchall()
    return [UserVisit(**row) for row in rows]


def find_by_id(user_id: int, visit_id: int) -> UserVisit | None:
    """Return one visit, but only if it belongs to this user."""
    row = conn.execute(
        "select * from user_visits where id = %s and user_id = %s and not void_sw",
        (visit_id, user_id),
    ).fetchone()
    return UserVisit(**row) if row else None


def create(user_id: int, appointment_id: int, summary: str) -> UserVisit:
    """Insert a visit with a short summary."""
    row = conn.execute(
        "insert into user_visits (user_id, appointment_id, summary, created_by, updated_by) "
        "values (%s, %s, %s, %s, %s) returning *",
        (user_id, appointment_id, summary, user_id, user_id),
    ).fetchone()
    return UserVisit(**row)
