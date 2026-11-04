from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserFact:
    id: int
    user_id: int
    fact: str
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
