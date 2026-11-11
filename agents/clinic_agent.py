from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command

from config.database import checkpoint_conn
from middleware import clinic_middlewares
from models.clinic_user import ClinicContext, ClinicUser
from prompts.prompts import SYSTEM_PROMPT
from tools import clinic_tools
from util.token_usage import get_token_usage
from util.tool_calls import get_tool_calls

# What the patient sees while the front desk checks a booking or an email.
PAUSED_REPLY = (
    "I've sent this to the front desk for a quick check. "
    "I'll reply here as soon as they answer."
)

# Conversation history lives in Postgres, so it survives a restart.
checkpointer = PostgresSaver(checkpoint_conn)
# creates the checkpoint tables if they don't exist yet
checkpointer.setup()

# One tool call at a time, so every pause has exactly one action for the front desk.
model = init_chat_model("openai:gpt-5.4", model_kwargs={"parallel_tool_calls": False})

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=clinic_tools,
    middleware=clinic_middlewares,
    context_schema=ClinicContext,
    checkpointer=checkpointer,
)


def build_result(result) -> dict:
    """Turn the agent's result into the dict that ask() and resume() return.

    `result` is a GraphOutput: result.value is the state (messages, intent, ...)
    and result.interrupts lists the pauses. It is empty when the agent finished.
    """
    state = result.value
    tool_calls = get_tool_calls(state["messages"])
    token_usage = get_token_usage(state["messages"])

    if result.interrupts:
        # Paused before book_appointment or send_email. The model makes one tool call
        # at a time, so there is only one action to approve.
        action = result.interrupts[0].value["action_requests"][0]
        paused = {"tool_name": action["name"], "args": action["args"]}
        reply = PAUSED_REPLY
        # The output guard runs at the end, so it has not checked anything yet.
        rejected_response = None
        new_response = None
    else:
        paused = None
        reply = state["messages"][-1].content
        rejected_response = state.get("rejected_response")
        new_response = state.get("new_response")

    return {
        "reply": reply,
        "tool_calls": tool_calls,
        "intent": state.get("intent"),
        "judge_reason": state.get("judge_reason"),
        "rejected_response": rejected_response,
        "new_response": new_response,
        "input_tokens": token_usage["input_tokens"],
        "output_tokens": token_usage["output_tokens"],
        "paused": paused,
    }


def ask(question: str, clinic_user: ClinicUser, thread_id: str) -> dict:
    """Send the user's question to the agent.

    Returns the reply, the tools it used and the tokens this turn cost:
    {"reply", "tool_calls", "intent", "judge_reason", "rejected_response",
    "new_response", "input_tokens", "output_tokens", "paused"}
    "paused" is {"tool_name", "args"} when the agent waits for the front desk, otherwise None.
    """
    result = agent.invoke(
        {"messages": [HumanMessage(question)]},
        config={"configurable": {"thread_id": thread_id}},
        context=ClinicContext(user=clinic_user),
        # this context is available to the agent through the execution context,
        # and can be used in the middleware to customize the agent's behavior based on the user
        version="v2",  # returns a GraphOutput with .value and .interrupts
    )
    return build_result(result)


def resume(decision: dict, clinic_user: ClinicUser, thread_id: str) -> dict:
    """Carry on a paused chat with the front desk's decision.

    `decision` is LangChain's format, for example {"type": "approve"}.
    The agent runs as the patient (clinic_user), not as the admin.
    Returns the same dict as ask().
    """
    result = agent.invoke(
        Command(resume={"decisions": [decision]}),
        config={"configurable": {"thread_id": thread_id}},
        context=ClinicContext(user=clinic_user),
        version="v2",
    )
    return build_result(result)
