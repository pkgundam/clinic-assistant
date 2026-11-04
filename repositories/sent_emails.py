from config.database import conn
from models.sent_email import SentEmail


def create(user_id: int, appointment_id: int, to_email: str, subject: str, body: str) -> SentEmail:
    """Record an email that was 'sent' (we only store it, there is no email server)."""
    row = conn.execute(
        "insert into sent_emails "
        "(user_id, appointment_id, to_email, subject, body, created_by, updated_by) "
        "values (%s, %s, %s, %s, %s, %s, %s) returning *",
        (user_id, appointment_id, to_email, subject, body, user_id, user_id),
    ).fetchone()
    return SentEmail(**row)
