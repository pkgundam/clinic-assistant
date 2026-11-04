from dataclasses import dataclass
from datetime import datetime


@dataclass
class Doctor:
    id: int
    full_name: str
    speciality_code: str
    speciality: str
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
