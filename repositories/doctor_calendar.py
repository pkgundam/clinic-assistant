from datetime import datetime

from config.database import conn
from models.doctor_calendar import DoctorCalendar


def get_open_slots(doctor_id: int, day_start: datetime, day_end: datetime) -> list[DoctorCalendar]:
    """Return the doctor's open slots between day_start and day_end that are still in the future."""
    rows = conn.execute(
        "select * from doctor_calendar "
        "where doctor_id = %s and status = 'open' and not void_sw "
        "and starts_at >= %s and starts_at < %s and starts_at > now() "
        "order by starts_at",
        (doctor_id, day_start, day_end),
    ).fetchall()
    return [DoctorCalendar(**row) for row in rows]


def book_if_open(calendar_id: int, user_id: int) -> DoctorCalendar | None:
    """Mark the slot booked, but only if it is still open and in the future. Returns None if not."""
    row = conn.execute(
        "update doctor_calendar set status = 'booked', updated_by = %s "
        "where id = %s and status = 'open' and not void_sw and starts_at > now() returning *",
        (user_id, calendar_id),
    ).fetchone()
    return DoctorCalendar(**row) if row else None


def set_open(calendar_id: int, user_id: int) -> None:
    """Put a slot back to open (used when an appointment is cancelled)."""
    conn.execute(
        "update doctor_calendar set status = 'open', updated_by = %s where id = %s",
        (user_id, calendar_id),
    )
