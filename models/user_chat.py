from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserChat:
    id: int
    user_id: int
    thread_id: str
    title: str | None  # empty until the LLM generates it
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
