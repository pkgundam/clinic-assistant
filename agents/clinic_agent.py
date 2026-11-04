from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from middleware import clinic_middlewares
from models.clinic_user import ClinicContext, ClinicUser
from prompts.prompts import SYSTEM_PROMPT
from tools import clinic_tools


agent = create_agent(
    model="openai:gpt-5.4",
    system_prompt=SYSTEM_PROMPT,
    tools=clinic_tools,
    middleware=clinic_middlewares,
    context_schema=ClinicContext,
    checkpointer=InMemorySaver(),  # short-term memory; moves to Postgres later
)


def ask(question: str, clinic_user: ClinicUser, thread_id: str) -> str:
    """Send the user's question to the agent and return its reply."""
    result = agent.invoke(
        {"messages": [HumanMessage(question)]},
        config={"configurable": {"thread_id": thread_id}},
        context=ClinicContext(user=clinic_user),
        # this context is available to the agent through the execution context,
        # and can be used in the middleware to customize the agent's behavior based on the user
    )
    return result["messages"][-1].content
