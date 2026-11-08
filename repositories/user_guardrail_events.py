from config.database import conn
from models.user_guardrail_event import UserGuardrailEvent


def create(user_id: int, thread_id: str, question: str, verdict) -> UserGuardrailEvent:
    """Record an emergency or an unsafe message. `verdict` is the judge's InputCheck."""
    row = conn.execute(
        "insert into user_guardrail_events "
        "(user_id, thread_id, question, safe, injection_type, emergency, intent, reason, "
        "created_by, updated_by) "
        "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning *",
        (
            user_id,
            thread_id,
            question,
            verdict.safe,
            verdict.injection_type,
            verdict.emergency,
            verdict.intent,
            verdict.reason,
            user_id,
            user_id,
        ),
    ).fetchone()
    return UserGuardrailEvent(**row)
