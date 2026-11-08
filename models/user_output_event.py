from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserOutputEvent:
    id: int
    user_id: int
    thread_id: str
    question: str
    reply: str
    tone_ok: bool
    medical_advice: bool
    diagnosis: bool
    promises: bool
    reveals_internals: bool
    tool_names_found: str | None  # the tool names found in the reply, comma separated
    reason: str
    rewritten_reply: str | None  # empty if the rewrite was not used
    escalated: bool
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
