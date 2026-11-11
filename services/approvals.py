from agents.clinic_agent import resume
from config.clinic import clinic_time
from models.user import User
from repositories import (
    doctor_calendar,
    user_appointments,
    user_approvals,
    user_chat_messages,
    users,
)
from services.auth import load_clinic_user
from tools.notification_tools import email_subject

# The front desk's choice -> the status we save in user_approvals.
STATUSES = {"approve": "approved", "edit": "edited", "reject": "rejected"}


class ApprovalNotFound(Exception):
    """There is no approval with this id."""


class AlreadyDecided(Exception):
    """The front desk already decided this approval."""


class ResumeFailed(Exception):
    """The agent could not carry on after the decision. The approval is pending again."""


def approval_details(user_id: int, tool_name: str, args: dict) -> dict | None:
    """What the front desk needs to read a request without ids: the doctor, the time, ...

    None if the slot or the booking code does not match anything.
    """
    if tool_name == "book_appointment":
        slot = doctor_calendar.find_slot_details(args.get("calendar_id"))
        if slot is None:
            return None
        return {
            "doctor_name": slot["doctor_name"],
            "speciality": slot["speciality"],
            "starts_at": slot["starts_at"],
            "starts_at_display": clinic_time(slot["starts_at"]),
            "reason": args.get("reason"),
        }

    if tool_name == "send_email":
        booking_code = str(args.get("booking_code", "")).strip().upper()
        appointment = user_appointments.find_details_by_booking_code(user_id, booking_code)
        if appointment is None:
            return None
        return {
            "booking_code": appointment["booking_code"],
            "doctor_name": appointment["doctor_name"],
            "speciality": appointment["speciality"],
            "starts_at": appointment["starts_at"],
            "starts_at_display": clinic_time(appointment["starts_at"]),
            "reason": appointment["reason"],
            "subject": email_subject(appointment["booking_code"]),
        }

    return None


def list_pending() -> list[dict]:
    """Every approval the front desk still has to decide, oldest first, with readable details.

    `args` stays as the agent wrote it (an edit starts from it), `details` is for reading.
    """
    approvals = []
    for row in user_approvals.find_pending():
        approvals.append(
            {
                "id": row["id"],
                "patient_name": row["patient_name"],
                "tool_name": row["tool_name"],
                "args": row["args"],
                "details": approval_details(row["user_id"], row["tool_name"], row["args"]),
                "created_at": row["created_at"],
            }
        )
    return approvals


def decide_approval(
    approval_id: int, decision: str, args: dict | None, reason: str | None, admin: User
) -> dict:
    """Save the front desk's decision and let the paused agent carry on.

    `decision` is "approve", "edit" or "reject". Edit needs `args` (only the fields
    that change), reject needs `reason`.
    Returns {"reply": ..., "waiting_for_approval": ...}.
    """
    approval = user_approvals.find_by_id(approval_id)
    if approval is None:
        raise ApprovalNotFound()

    # 1. the decision in LangChain's format
    edited_args = None
    reject_reason = None
    if decision == "approve":
        langchain_decision = {"type": "approve"}
    elif decision == "edit":
        # The admin only sends what he changes. Everything else keeps the agent's values.
        edited_args = {**approval.args, **args}
        langchain_decision = {
            "type": "edit",
            "edited_action": {"name": approval.tool_name, "args": edited_args},
        }
    else:
        reject_reason = reason
        # The model reads this as "User rejected the tool call ... with reason: ...",
        # so we say that it was the front desk, not the patient.
        langchain_decision = {
            "type": "reject",
            "message": f"The clinic's front desk did not approve this. Their reason: {reject_reason}",
        }

    # 2. save the decision first. Only a pending approval can be decided,
    # so two clicks on the same approval (even at the same moment) never run the tool twice.
    if not user_approvals.decide(
        approval.id, STATUSES[decision], edited_args, reject_reason, admin.id
    ):
        raise AlreadyDecided()

    # 3. the agent carries on as the patient, not as the admin
    patient = load_clinic_user(users.find_by_id(approval.user_id))
    try:
        result = resume(langchain_decision, patient, approval.thread_id)
    except Exception as error:
        # Something broke (for example OpenAI was down). The paused chat is still saved
        # in Postgres, so we put the approval back to pending and the front desk can try again.
        print(f"[approvals] resume failed for approval {approval.id}: {error!r}")
        user_approvals.reopen(approval.id)
        raise ResumeFailed() from error

    # 4. paused again (send_email after the booking): one more row for the front desk.
    # The patient's question still has no answer, so it is the same chat message.
    if result["paused"]:
        user_approvals.create(
            approval.user_id,
            approval.thread_id,
            approval.chat_message_id,
            result["paused"]["tool_name"],
            result["paused"]["args"],
        )
    else:
        # finished: now the patient's question gets its answer
        user_chat_messages.save_answer(
            approval.chat_message_id,
            result["reply"],
            result["input_tokens"],
            result["output_tokens"],
            admin.id,
        )

    return {
        "reply": result["reply"],
        "waiting_for_approval": result["paused"] is not None,
    }
