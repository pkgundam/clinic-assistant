from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver

from config.database import checkpoint_conn
from middleware import clinic_middlewares
from models.clinic_user import ClinicContext, ClinicUser
from prompts.prompts import SYSTEM_PROMPT
from tools import clinic_tools
from util.token_usage import get_token_usage
from util.tool_calls import get_tool_calls

# Conversation history lives in Postgres, so it survives a restart.
checkpointer = PostgresSaver(checkpoint_conn)
# creates the checkpoint tables if they don't exist yet
checkpointer.setup()

agent = create_agent(
    model="openai:gpt-5.4",
    system_prompt=SYSTEM_PROMPT,
    tools=clinic_tools,
    middleware=clinic_middlewares,
    context_schema=ClinicContext,
    checkpointer=checkpointer,
)


def ask(question: str, clinic_user: ClinicUser, thread_id: str) -> dict:
    """Send the user's question to the agent.

    Returns the reply, the tools it used and the tokens this turn cost:
    {"reply", "tool_calls", "intent", "judge_reason", "input_tokens", "output_tokens"}
    """
    result = agent.invoke(
        {"messages": [HumanMessage(question)]},
        config={"configurable": {"thread_id": thread_id}},
        context=ClinicContext(user=clinic_user),
        # this context is available to the agent through the execution context,
        # and can be used in the middleware to customize the agent's behavior based on the user
    )
    llm_answer = result["messages"][-1].content
    tool_calls = get_tool_calls(result["messages"])
    token_usage = get_token_usage(result["messages"])

    return {
        "reply": llm_answer,
        "tool_calls": tool_calls,
        "intent": result["intent"],
        "judge_reason": result["judge_reason"],
        "input_tokens": token_usage["input_tokens"],
        "output_tokens": token_usage["output_tokens"],
    }
