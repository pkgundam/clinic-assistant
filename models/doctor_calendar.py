from dataclasses import dataclass
from datetime import datetime


@dataclass
class DoctorCalendar:
    id: int
    doctor_id: int
    starts_at: datetime
    ends_at: datetime
    status: str  # open, booked or leave
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
