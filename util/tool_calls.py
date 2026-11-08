import json

from langchain.messages import AIMessage, HumanMessage, ToolMessage


def get_tool_calls(messages: list) -> list[dict]:
    """Return the tools the agent used in this turn, each with its args and result.

    `messages` is the whole conversation, so we only look at the messages after
    the last HumanMessage (the question that was just asked).
    """
    last_question = max(
        i for i, m in enumerate(messages) if isinstance(m, HumanMessage)
    )
    this_turn = messages[last_question + 1 :]

    # What each tool returned, found by the id that links it to its tool call.
    results = {
        m.tool_call_id: m.content for m in this_turn if isinstance(m, ToolMessage)
    }

    def as_dict(content):
        """Tool results are JSON text. Turn them back into a dict (plain text stays text)."""
        try:
            return json.loads(content)
        except (TypeError, ValueError):
            return content

    tool_calls = []
    for message in this_turn:
        if isinstance(message, AIMessage):
            for call in message.tool_calls:
                tool_calls.append(
                    {
                        "name": call["name"],
                        "args": call["args"],
                        "result": as_dict(results.get(call["id"])),
                    }
                )
    return tool_calls
