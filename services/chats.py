from langchain.chat_models import init_chat_model

from agents.clinic_agent import ask
from models.clinic_user import ClinicUser
from repositories import user_approvals, user_chat_messages, user_chats
from util.redact import redact

title_model = init_chat_model("openai:gpt-5.4")

STILL_WAITING_REPLY = (
    "We're still waiting on the front desk. I'll reply here as soon as they answer."
)


def generate_title(question: str) -> str:
    """Ask the LLM for a short title (3 to 6 words) for a chat that starts with this question."""
    prompt = (
        "Write a title of 3 to 6 words for a clinic chat that starts with this "
        "patient message. Reply with only the title, no quotes and no full stop.\n\n"
        f"Patient message: {question}"
    )
    return title_model.invoke(prompt).content.strip().strip('"').rstrip(".")


def ask_and_save(question: str, clinic_user: ClinicUser, thread_id: str) -> dict:
    """Ask the agent and save the chat.

    Returns {"reply": ..., "tool_calls": [...], "intent": ..., "judge_reason": ...,
    "rejected_response": ..., "new_response": ..., "waiting_for_approval": ...}.
    """
    # 0. Hide any social security number first, so it is never saved
    # and never reaches the judge, the agent or the title model.
    question = redact(question)

    # A paused chat has a tool call with no result yet, and OpenAI errors if we send
    # a new message on top of it. So we don't save it and don't call the agent.
    if user_approvals.is_waiting(thread_id):
        return {
            "reply": STILL_WAITING_REPLY,
            "tool_calls": [],
            "intent": None,
            "judge_reason": None,
            "rejected_response": None,
            "new_response": None,
            "waiting_for_approval": True,
        }

    user_id = clinic_user.profile.id

    # 1. create a new chat if this is the first message in this thread,
    # or load the existing chat
    chat = user_chats.save(user_id, thread_id)
    # 2. store the question in the user_chat_messages table, and get the message
    message = user_chat_messages.create(chat.id, question, user_id)
    # 3. ask the agent and get the answer, tools used, and token usage
    result = ask(question, clinic_user, thread_id)
    # 4. paused before book_appointment or send_email: save it for the front desk.
    # The answer stays empty until they decide (services/approvals.py saves it then).
    if result["paused"]:
        user_approvals.create(
            user_id,
            thread_id,
            message.id,
            result["paused"]["tool_name"],
            result["paused"]["args"],
        )
    else:
        # store the answer in the user_chat_messages table
        user_chat_messages.save_answer(
            message.id,
            result["reply"],
            result["input_tokens"],
            result["output_tokens"],
            user_id,
        )

    # 5. Only the first answer of a chat needs a title, and only if the agent ran.
    # The judge's fixed replies have no token counts, so 0 means the agent never ran.
    if chat.title is None and result["input_tokens"] > 0:
        chat_title = generate_title(question)
        user_chats.save_title(chat.id, chat_title, user_id)

    return {
        "reply": result["reply"],
        "tool_calls": result["tool_calls"],
        "intent": result["intent"],
        "judge_reason": result["judge_reason"],
        "rejected_response": result["rejected_response"],
        "new_response": result["new_response"],
        "waiting_for_approval": result["paused"] is not None,
    }
