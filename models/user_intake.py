from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserIntake:
    id: int
    user_id: int
    appointment_id: int | None
    thread_id: str
    question_key: str
    question: str
    answer: str
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
