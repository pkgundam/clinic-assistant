from config.database import conn
from models.user import User


def find_by_email(email: str) -> User | None:
    """Return the active user with this email, or None if there isn't one."""
    row = conn.execute(
        "select * from users where email = %s and not void_sw",
        (email,),
    ).fetchone()
    return User(**row) if row else None


def find_by_id(user_id: int) -> User | None:
    """Return the active user with this id, or None if there isn't one."""
    row = conn.execute(
        "select * from users where id = %s and not void_sw",
        (user_id,),
    ).fetchone()
    return User(**row) if row else None
