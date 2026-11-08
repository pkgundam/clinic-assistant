from config.database import conn
from models.user_output_event import UserOutputEvent


def create(
    user_id: int,
    thread_id: str,
    question: str,
    reply: str,
    verdict,
    tool_names_found: list[str],
    rewritten_reply: str,
    escalated: bool,
) -> UserOutputEvent:
    """Record a reply that failed the output check. `verdict` is the judge's OutputCheck."""
    row = conn.execute(
        "insert into user_output_events "
        "(user_id, thread_id, question, reply, tone_ok, medical_advice, diagnosis, promises, "
        "reveals_internals, tool_names_found, reason, rewritten_reply, escalated, "
        "created_by, updated_by) "
        "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning *",
        (
            user_id,
            thread_id,
            question,
            reply,
            verdict.tone_ok,
            verdict.medical_advice,
            verdict.diagnosis,
            verdict.promises,
            verdict.reveals_internals,
            ", ".join(tool_names_found) or None,  # empty list -> null
            verdict.reason,
            rewritten_reply,
            escalated,
            user_id,
            user_id,
        ),
    ).fetchone()
    return UserOutputEvent(**row)
