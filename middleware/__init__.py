from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware,
)

from middleware.input_guardrails_middleware import input_guardrails
from middleware.output_guardrails_middleware import output_guardrails
from middleware.rolling_summary_middleware import summarize_old_messages
from middleware.tool_errors_middleware import handle_tool_errors
from middleware.user_profile_middleware import user_profile_middleware

# Limits are per question. A reschedule is one cancel and one book, so it still works.
limit_middlewares = [
    ToolCallLimitMiddleware(tool_name="book_appointment", run_limit=1),
    ToolCallLimitMiddleware(tool_name="cancel_appointment", run_limit=1),
    ToolCallLimitMiddleware(tool_name="send_email", run_limit=1),
    # The agent loop can never run forever. The model makes one tool call at a time
    # (see agents/clinic_agent.py), so a long intake in one message needs more calls.
    ModelCallLimitMiddleware(run_limit=25),
]

# Human in the loop: the agent pauses before these tools run, and the front desk
# approves, edits or rejects the call. Every other tool runs without a pause.
human_in_the_loop = HumanInTheLoopMiddleware(
    interrupt_on={
        "book_appointment": {"allowed_decisions": ["approve", "edit", "reject"]},
        "send_email": {"allowed_decisions": ["approve", "edit", "reject"]},
    }
)

# Every middleware we create is added to this list and given to the agent.
clinic_middlewares = [
    input_guardrails,
    user_profile_middleware,
    summarize_old_messages,
    handle_tool_errors,
    *limit_middlewares,
    human_in_the_loop,
    output_guardrails,
]
