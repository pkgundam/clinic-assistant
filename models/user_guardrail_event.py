from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserGuardrailEvent:
    id: int
    user_id: int
    thread_id: str
    question: str
    safe: bool
    injection_type: str
    emergency: bool
    intent: str
    reason: str
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
