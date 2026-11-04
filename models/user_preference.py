from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserPreference:
    id: int
    user_id: int
    preference: str
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
