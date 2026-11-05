from config.database import conn
from models.user_chat_message import UserChatMessage


def create(chat_id: int, question: str, user_id: int) -> UserChatMessage:
    """Insert a message with just the question. The answer is added later by save_answer."""
    row = conn.execute(
        "insert into user_chat_messages (chat_id, question, created_by, updated_by) "
        "values (%s, %s, %s, %s) returning *",
        (chat_id, question, user_id, user_id),
    ).fetchone()
    return UserChatMessage(**row)


def find_by_chat(chat_id: int) -> list[UserChatMessage]:
    """Return all the messages of a chat, oldest first."""
    rows = conn.execute(
        "select * from user_chat_messages where chat_id = %s and not void_sw "
        "order by message_sent_at, id",
        (chat_id,),
    ).fetchall()

    messages = []
    for row in rows:
        messages.append(UserChatMessage(**row))
    return messages


def save_answer(
    message_id: int, ai_answer: str, input_tokens: int, output_tokens: int, user_id: int
) -> None:
    """Add the answer, the token counts and the time the answer arrived."""
    conn.execute(
        "update user_chat_messages set ai_answer = %s, input_tokens = %s, output_tokens = %s, "
        "response_recvd_at = now(), updated_at = now(), updated_by = %s where id = %s",
        (ai_answer, input_tokens, output_tokens, user_id, message_id),
    )
