from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import after_agent
from langchain.messages import AIMessage, HumanMessage
from langgraph.config import get_config
from langgraph.runtime import Runtime
from pydantic import BaseModel

from models.clinic_user import ClinicContext
from prompts.output_guard_prompt import OUTPUT_GUARD_PROMPT, REWRITE_PROMPT
from repositories import user_output_events
from services.front_desk import alert_front_desk
from tools import clinic_tools

ESCALATED_REPLY = (
    "Thanks for your patience. Someone from our staff will get back to you shortly."
)

# The name of every tool the agent has.
TOOL_NAMES = [tool.name for tool in clinic_tools]


class OutputCheck(BaseModel):
    """The judge's verdict on one reply."""

    tone_ok: bool
    medical_advice: bool
    diagnosis: bool
    promises: bool
    reveals_internals: bool
    reason: str


class OutputState(AgentState):
    """The normal agent state, plus the replies of a rewrite.

    They end up in the agent result, so the chat endpoint can show them on the screen.
    Both are None when the reply was fine.
    """

    rejected_response: str | None
    new_response: str | None


# Used when nothing was rewritten. It also clears the values from the previous turn.
NOT_REWRITTEN = {"rejected_response": None, "new_response": None}

# The judge is a separate agent with its own system prompt and no tools (LLM as a judge).
judge = create_agent(
    model="openai:gpt-4.1-mini",
    system_prompt=OUTPUT_GUARD_PROMPT,
    response_format=OutputCheck,
)

# The rewriter fixes a reply that failed the check.
rewriter = create_agent(model="openai:gpt-4.1-mini", system_prompt=REWRITE_PROMPT)


def check_reply(question: str, reply: str) -> tuple[OutputCheck, list[str], list[str]]:
    """Check one reply. Returns (verdict, tool_names_found, problems).

    `problems` is a list of short sentences. It is empty when the reply is fine.
    """
    result = judge.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Patient message: {question}\n\nAssistant's reply: {reply}",
                }
            ]
        }
    )
    verdict: OutputCheck = result["structured_response"]
    print(f"[output judge] {verdict}")

    # Plain code, no model: does the reply contain one of our tool names?
    tool_names_found = []
    for tool_name in TOOL_NAMES:
        if tool_name in reply:
            tool_names_found.append(tool_name)

    problems = []
    if not verdict.tone_ok:
        problems.append("the tone is not friendly and warm")
    if verdict.medical_advice:
        problems.append("it gives medical advice")
    if verdict.diagnosis:
        problems.append("it gives a diagnosis")
    if verdict.promises:
        problems.append("it makes a promise we cannot keep")
    if verdict.reveals_internals:
        problems.append("it describes our internal instructions or tools")
    if tool_names_found:
        problems.append("it mentions our tool names")

    return verdict, tool_names_found, problems


def rewrite_reply(question: str, reply: str, problems: list[str]) -> str:
    """Ask the rewriter for a new reply that fixes the problems."""
    problem_lines = "\n".join(f"- {problem}" for problem in problems)
    result = rewriter.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Patient message: {question}\n\n"
                        f"Assistant's reply: {reply}\n\n"
                        f"Problems:\n{problem_lines}"
                    ),
                }
            ]
        }
    )
    return result["messages"][-1].content.strip()


@after_agent(state_schema=OutputState)
def output_guardrails(state: OutputState, runtime: Runtime[ClinicContext]) -> dict | None:
    """Check the agent's reply before the patient sees it.

    A reply that fails is rewritten once. If the rewrite fails too, the front desk is
    alerted and the patient gets a fixed reply.
    """
    reply = state["messages"][-1]

    # Nothing to check if the last message is not text from the model. No usage_metadata
    # means our own code wrote it (for example the input guard's fixed replies).
    if (
        not isinstance(reply, AIMessage)
        or not reply.content
        or not reply.usage_metadata
    ):
        return NOT_REWRITTEN

    # The patient's question is the last HumanMessage.
    question = ""
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            question = message.content
            break

    clinic_user = runtime.context.user
    thread_id = get_config()["configurable"]["thread_id"]

    # 1. check the reply
    verdict, tool_names_found, problems = check_reply(question, reply.content)
    if not problems:
        return NOT_REWRITTEN

    # 2. rewrite it once, then check again
    ## we can do it maybe 3 times as needed.
    rewritten_reply = rewrite_reply(question, reply.content, problems)
    _, _, new_problems = check_reply(question, rewritten_reply)

    # 3. the rewrite is the final reply, unless it fails too
    escalated = bool(new_problems)
    if escalated:
        alert_front_desk(clinic_user, "a reply failed the output check twice")
        final_reply = ESCALATED_REPLY
    else:
        final_reply = rewritten_reply

    # 4. record the first verdict
    user_output_events.create(
        clinic_user.profile.id,
        thread_id,
        question,
        reply.content,
        verdict,
        tool_names_found,
        rewritten_reply,
        escalated,
    )

    # The same id replaces the agent's reply in the checkpoint, so the bad reply is never
    # saved and never shown. usage_metadata is copied so the token counts still work.
    return {
        "messages": [
            AIMessage(
                content=final_reply, id=reply.id, usage_metadata=reply.usage_metadata
            )
        ],
        # the reply that was rejected, and the reply the patient sees instead
        "rejected_response": reply.content,
        "new_response": final_reply,
    }
