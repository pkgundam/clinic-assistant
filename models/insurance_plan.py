from dataclasses import dataclass
from datetime import datetime


@dataclass
class InsurancePlan:
    id: int
    code: str
    name: str
    accepted: bool
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
