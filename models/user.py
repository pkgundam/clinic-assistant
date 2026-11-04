from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class User:
    id: int
    role: str
    full_name: str
    email: str
    phone: str | None
    date_of_birth: date | None
    insurance_plan_id: int | None
    insurance_member_id: str | None
    password_hash: str | None
    created_at: datetime
    created_by: int | None
    updated_at: datetime
    updated_by: int | None
    void_sw: bool
