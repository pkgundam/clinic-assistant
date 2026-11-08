import json

from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage

from tools.errors import ToolError


def error_message(message: str, tool_name: str, tool_call_id: str) -> ToolMessage:
    """A failed tool result, in the same shape as a success: {"status": "error", "message": ...}"""
    content = json.dumps({"status": "error", "message": message})
    return ToolMessage(content=content, name=tool_name, tool_call_id=tool_call_id, status="error")


@wrap_tool_call
def handle_tool_errors(request, handler):
    """Run every tool call inside a try/except, so a broken tool never crashes the chat.

    The result always has a status: "success" or "error".
    """
    tool_name = request.tool_call["name"]
    tool_call_id = request.tool_call["id"]

    try:
        # The tool ran fine. Its ToolMessage comes back with status "success".
        return handler(request)
    except ToolError as error:
        # The tool said no on purpose. Its message tells the model what to say.
        return error_message(str(error), tool_name, tool_call_id)
    except Exception as error:
        # A bug. Print the real error for us, and give the model a safe message.
        print(f"[tool error] {tool_name} failed: {error!r}")
        return error_message(
            "Something went wrong with this tool. Tell the patient we could not do it "
            "right now and offer to try again.",
            tool_name,
            tool_call_id,
        )
