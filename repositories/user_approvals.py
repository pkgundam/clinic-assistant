from psycopg.types.json import Jsonb

from config.database import conn
from models.user_approval import UserApproval


def create(
    user_id: int, thread_id: str, chat_message_id: int, tool_name: str, args: dict
) -> UserApproval:
    """Save a pause: the agent wants to run this tool and waits for the front desk."""
    row = conn.execute(
        "insert into user_approvals "
        "(user_id, thread_id, chat_message_id, tool_name, args, created_by, updated_by) "
        "values (%s, %s, %s, %s, %s, %s, %s) returning *",
        (user_id, thread_id, chat_message_id, tool_name, Jsonb(args), user_id, user_id),
    ).fetchone()
    return UserApproval(**row)


def find_by_id(approval_id: int) -> UserApproval | None:
    """Return the approval with this id, or None if there isn't one."""
    row = conn.execute(
        "select * from user_approvals where id = %s and not void_sw",
        (approval_id,),
    ).fetchone()
    return UserApproval(**row) if row else None


def find_pending() -> list[dict]:
    """Every approval the front desk still has to decide, with the patient's name, oldest first."""
    return conn.execute(
        "select a.id, a.user_id, u.full_name as patient_name, a.tool_name, a.args, a.created_at "
        "from user_approvals a "
        "join users u on u.id = a.user_id "
        "where a.status = 'pending' and not a.void_sw "
        "order by a.created_at, a.id"
    ).fetchall()


def is_waiting(thread_id: str) -> bool:
    """Is this chat waiting for the front desk?

    True from the first pause until the final reply is saved: the chat has an approval
    whose question has no answer yet. This stays true while the agent is still running
    after a decision, so the patient keeps waiting until the reply is really there.
    """
    row = conn.execute(
        "select exists ("
        "  select 1 from user_approvals a "
        "  join user_chat_messages m on m.id = a.chat_message_id "
        "  where a.thread_id = %s and not a.void_sw and m.ai_answer is null"
        ") as waiting",
        (thread_id,),
    ).fetchone()
    return row["waiting"]


def decide(
    approval_id: int,
    status: str,
    edited_args: dict | None,
    reject_reason: str | None,
    admin_id: int,
) -> bool:
    """Save the front desk's decision: approved, edited or rejected.

    Only a pending approval is updated, so the same approval can never be decided twice.
    Returns True if it was updated, False if it was already decided.
    """
    cursor = conn.execute(
        "update user_approvals set status = %s, edited_args = %s, reject_reason = %s, "
        "decided_by = %s, decided_at = now(), updated_at = now(), updated_by = %s "
        "where id = %s and status = 'pending' and not void_sw",
        (
            status,
            Jsonb(edited_args) if edited_args is not None else None,
            reject_reason,
            admin_id,
            admin_id,
            approval_id,
        ),
    )
    return cursor.rowcount == 1


def reopen(approval_id: int) -> None:
    """Put a decided approval back to pending, so the front desk can decide it again.

    Used when the agent failed to carry on after the decision.
    """
    conn.execute(
        "update user_approvals set status = 'pending', edited_args = null, "
        "reject_reason = null, decided_by = null, decided_at = null, updated_at = now() "
        "where id = %s",
        (approval_id,),
    )
