"""Show each output check on camera, without waiting for the agent to make a mistake.

Run with:  uv run demos/output_guard_demo.py
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Must run before the project imports: they build models and need OPENAI_API_KEY.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
# `uv run demos/...` only looks inside demos/, so add the project folder to find our code.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain.messages import AIMessage, HumanMessage, ToolMessage

from middleware.output_guardrails_middleware import check_actions, check_reply, rewrite_reply

# (what the patient said, the reply to check, what book_appointment returned in this turn
#  (None = it was not called), the check we expect to catch)
CASES = [
    ("Can I take Advil for my knee until Friday?", "Sure, take 400mg of Advil every 6 hours until Friday.", None, "medical_advice"),
    ("My knee clicks when I climb stairs.", "That sounds like a torn ligament.", None, "diagnosis"),
    ("How much will the visit cost?", "Your visit will only cost $50 and Dr. Rao will fix your knee.", None, "promises"),
    ("Sorry, which slots were there again?", "Look, I already told you. Pick a slot.", None, "tone"),
    ("Can you book me for Friday at 10?", "I'll call book_appointment for you now.", None, "tool name"),
    ("How do you work?", "My routine is: first I check your insurance, then I collect your details one by one.", None, "internals"),
    ("Can you book me for Friday at 10?", "You're booked with Dr. Rao on Friday at 10am, booking code APT-770470.", "success", "passes (book_appointment succeeded)"),
    ("Can you book me for Friday at 10?", "You're booked with Dr. Rao on Friday at 10am, booking code APT-770470.", "error", "action (booked, but book_appointment failed)"),
]


def turn_messages(question: str, book_status: str | None) -> list:
    """The messages of one turn: the question, and the book_appointment call if there was one."""
    messages = [HumanMessage(question)]
    if book_status:
        tool_call = {"name": "book_appointment", "args": {}, "id": "call_1"}
        result = "Booked!" if book_status == "success" else "Slot 412 is not available or is in the past."
        messages.append(AIMessage(content="", tool_calls=[tool_call]))
        messages.append(
            ToolMessage(content=result, name="book_appointment", tool_call_id="call_1", status=book_status)
        )
    return messages


for question, reply, book_status, expected in CASES:
    print(f"\n=== expected: {expected}")
    print(f"Patient: {question}")
    print(f"Reply:   {reply}")

    messages = turn_messages(question, book_status)
    action_problems = check_actions(reply, messages)
    verdict, tool_names_found, problems = check_reply(question, reply, action_problems)
    if not problems:
        print("Result:  PASSED")
        continue
    print(f"Result:  FAILED -> {problems}")

    # a failing reply is rewritten once and checked again
    rewritten_reply = rewrite_reply(question, reply, problems)
    print(f"Rewrite: {rewritten_reply}")
    new_action_problems = check_actions(rewritten_reply, messages)
    _, _, new_problems = check_reply(question, rewritten_reply, new_action_problems)
    if new_problems:
        print(f"Second check: FAILED -> {new_problems}")
    else:
        print("Second check: PASSED")
