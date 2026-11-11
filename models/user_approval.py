from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserApproval:
    id: int
    user_id: int  # the patient
    thread_id: str
    chat_message_id: int  # the question that is waiting for its answer
    tool_name: str  # book_appointment or send_email
    args: dict  # the tool's arguments, as the agent wrote them
    status: str  # pending, approved, edited or rejected
    edited_args: dict | None  # set when the front desk edited the arguments
    reject_reason: str | None  # set when the front desk rejected it
    decided_by: int | None  # the admin who decided
    decided_at: datetime | None
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
