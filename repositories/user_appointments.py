from config.database import conn
from models.user_appointment import UserAppointment

# An appointment together with its doctor and slot time. Each row is a dict with:
# id, booking_code, status, reason, calendar_id, doctor_name, speciality, starts_at
DETAILS_SQL = (
    "select a.id, a.booking_code, a.status, a.reason, a.calendar_id, "
    "d.full_name as doctor_name, d.speciality, c.starts_at "
    "from user_appointments a "
    "join doctor_calendar c on c.id = a.calendar_id "
    "join doctors d on d.id = c.doctor_id "
    "where a.user_id = %s and not a.void_sw"
)


def create(user_id: int, calendar_id: int, reason: str) -> UserAppointment:
    """Insert an appointment. The database makes the booking code."""
    row = conn.execute(
        "insert into user_appointments (user_id, calendar_id, reason, created_by, updated_by) "
        "values (%s, %s, %s, %s, %s) returning *",
        (user_id, calendar_id, reason, user_id, user_id),
    ).fetchone()
    return UserAppointment(**row)


def get_details_by_user(user_id: int) -> list[dict]:
    """Return all of this user's appointments with doctor and slot time, by slot time."""
    return conn.execute(DETAILS_SQL + " order by c.starts_at", (user_id,)).fetchall()


def find_all_details() -> list[dict]:
    """Return every appointment in the clinic, for every patient, ordered by slot time.

    Each row is a dict with: booking_code, status, reason, patient_name, doctor_name, starts_at
    """
    return conn.execute(
        "select a.booking_code, a.status, a.reason, u.full_name as patient_name, "
        "d.full_name as doctor_name, c.starts_at "
        "from user_appointments a "
        "join users u on u.id = a.user_id "
        "join doctor_calendar c on c.id = a.calendar_id "
        "join doctors d on d.id = c.doctor_id "
        "where not a.void_sw "
        "order by c.starts_at"
    ).fetchall()


def find_details_by_booking_code(user_id: int, booking_code: str) -> dict | None:
    """Return one appointment's details, but only if it belongs to this user."""
    return conn.execute(
        DETAILS_SQL + " and a.booking_code = %s",
        (user_id, booking_code),
    ).fetchone()


def cancel(appointment_id: int, user_id: int) -> None:
    """Mark the appointment cancelled."""
    conn.execute(
        "update user_appointments set status = 'cancelled', updated_by = %s where id = %s",
        (user_id, appointment_id),
    )
