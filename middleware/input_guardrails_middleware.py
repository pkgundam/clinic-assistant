from typing import Literal

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import before_agent
from langchain.messages import AIMessage
from langgraph.config import get_config
from langgraph.runtime import Runtime
from pydantic import BaseModel

from models.clinic_user import ClinicContext
from prompts.input_guard_prompt import INPUT_GUARD_PROMPT
from repositories import user_guardrail_events
from services.front_desk import alert_front_desk

EMERGENCY_REPLY = (
    "This sounds like it could be an emergency. I've alerted our clinic staff right now. "
    "If it's urgent, please call 911 or go to the nearest emergency room."
)
BLOCKED_REPLY = (
    "Sorry, I can't help with that. "
    "I can help with your appointments and questions about the clinic."
)
# Fixed replies for the intents the agent should not handle.
INTENT_REPLIES = {
    "lab_report": "I can't read lab reports yet. A doctor will go through them at your appointment.",
    "off_topic": "I can only help with your appointments and questions about the clinic.",
}


class InputCheck(BaseModel):
    """The judge's verdict on one patient message."""

    safe: bool
    injection_type: Literal[
        "none",
        "direct_override",
        "role_play",
        "prompt_leak",
        "data_exfiltration",
        "obfuscated",
        "unknown",
    ]
    emergency: bool
    intent: Literal[
        "appointments", "clinic_question", "past_visits", "lab_report", "off_topic"
    ]
    reason: str


class GuardedState(AgentState):
    """The normal agent state, plus the judge's intent and reason.

    They end up in the agent result, so the chat endpoint can show them on the screen.
    """

    intent: str
    judge_reason: str


# The judge is a separate agent with its own system prompt and no tools (LLM as a judge).
guard = create_agent(
    model="openai:gpt-4.1-mini",
    system_prompt=INPUT_GUARD_PROMPT,
    response_format=InputCheck,
)


@before_agent(state_schema=GuardedState, can_jump_to=["end"])
def input_guardrails(
    state: GuardedState, runtime: Runtime[ClinicContext]
) -> dict | None:
    """Check the patient's message before the agent sees it.

    Returns None to let the agent run. Returns a fixed reply plus jump_to "end"
    to answer right away, so the agent never runs.
    """
    clinic_user = runtime.context.user
    thread_id = get_config()["configurable"]["thread_id"]

    # The patient's new message is the last one. The assistant's last question is the
    # last AI message before it that has text (a tool call has no text).
    question = state["messages"][-1].content
    last_assistant_message = "(none, this is the first message)"
    for message in reversed(state["messages"][:-1]):
        if isinstance(message, AIMessage) and message.content:
            last_assistant_message = message.content
            break

    # Send both, so a short answer like "yes" is understood.
    result = guard.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"User's role: {clinic_user.profile.role}\n\n"
                        f"Assistant's last question: {last_assistant_message}\n\n"
                        f"Patient message: {question}"
                    ),
                }
            ]
        }
    )
    verdict: InputCheck = result["structured_response"]
    print(f"[input judge] {verdict}")

    # The verdict is put in the state, so the chat endpoint can show it.
    verdict_info = {"intent": verdict.intent, "judge_reason": verdict.reason}

    # 1. Emergency comes first, even if the message also tries to trick us.
    if verdict.emergency:
        user_guardrail_events.create(
            clinic_user.profile.id, thread_id, question, verdict
        )
        alert_front_desk(clinic_user, "may have an emergency")
        return {
            "messages": [AIMessage(content=EMERGENCY_REPLY)],
            "jump_to": "end",
            **verdict_info,
        }

    # 2. Not safe.
    if not verdict.safe:
        user_guardrail_events.create(
            clinic_user.profile.id, thread_id, question, verdict
        )
        return {
            "messages": [AIMessage(content=BLOCKED_REPLY)],
            "jump_to": "end",
            **verdict_info,
        }

    # 3. Lab reports and off topic questions get a fixed reply.
    if verdict.intent in INTENT_REPLIES:
        user_guardrail_events.create(
            clinic_user.profile.id, thread_id, question, verdict
        )
        reply = INTENT_REPLIES[verdict.intent]
        return {
            "messages": [AIMessage(content=reply)],
            "jump_to": "end",
            **verdict_info,
        }

    # 4. Everything else: no jump, so the agent runs.
    return verdict_info
