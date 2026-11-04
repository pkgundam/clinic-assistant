from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserAppointment:
    id: int
    booking_code: str
    user_id: int
    calendar_id: int
    reason: str | None
    status: str  # booked or cancelled
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
