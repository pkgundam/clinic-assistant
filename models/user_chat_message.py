from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserChatMessage:
    id: int
    chat_id: int
    question: str
    ai_answer: str | None  # empty until the answer arrives
    message_sent_at: datetime
    response_recvd_at: datetime | None
    input_tokens: int | None
    output_tokens: int | None
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    void_sw: bool
