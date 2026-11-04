from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserNote:
    id: int
    user_id: int
    note: str
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
