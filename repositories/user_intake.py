from config.database import conn
from models.user_intake import UserIntake


def get_open(user_id: int, thread_id: str) -> list[UserIntake]:
    """Return the answers saved in this chat that are not linked to an appointment yet."""
    rows = conn.execute(
        "select * from user_intake "
        "where user_id = %s and thread_id = %s and appointment_id is null and not void_sw "
        "order by id",
        (user_id, thread_id),
    ).fetchall()
    return [UserIntake(**row) for row in rows]


def get_by_appointment(appointment_id: int) -> list[UserIntake]:
    """Return the intake answers that were linked to this appointment."""
    rows = conn.execute(
        "select * from user_intake where appointment_id = %s and not void_sw order by id",
        (appointment_id,),
    ).fetchall()
    return [UserIntake(**row) for row in rows]


def save(user_id: int, thread_id: str, question_key: str, question: str, answer: str) -> UserIntake:
    """Update the answer if this question was already answered in this chat, otherwise insert it."""
    existing = conn.execute(
        "select id from user_intake "
        "where user_id = %s and thread_id = %s and question_key = %s "
        "and appointment_id is null and not void_sw",
        (user_id, thread_id, question_key),
    ).fetchone()

    if existing:
        row = conn.execute(
            "update user_intake set question = %s, answer = %s, updated_by = %s "
            "where id = %s returning *",
            (question, answer, user_id, existing["id"]),
        ).fetchone()
    else:
        row = conn.execute(
            "insert into user_intake "
            "(user_id, thread_id, question_key, question, answer, created_by, updated_by) "
            "values (%s, %s, %s, %s, %s, %s, %s) returning *",
            (user_id, thread_id, question_key, question, answer, user_id, user_id),
        ).fetchone()
    return UserIntake(**row)


def link_to_appointment(user_id: int, thread_id: str, appointment_id: int) -> None:
    """Attach this chat's open intake answers to the appointment that was just booked."""
    conn.execute(
        "update user_intake set appointment_id = %s, updated_by = %s "
        "where user_id = %s and thread_id = %s and appointment_id is null and not void_sw",
        (appointment_id, user_id, user_id, thread_id),
    )
