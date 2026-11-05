from langchain.messages import AIMessage, HumanMessage


def get_token_usage(messages: list) -> dict:
    """Add up the tokens the model used in this turn: {"input_tokens": ..., "output_tokens": ...}.

    `messages` is the whole conversation, so we only count the AI messages after
    the last HumanMessage. A turn can have several (one per model call, for example
    when the agent uses a tool and then answers).
    """
    # Find the position of the last question the patient asked.
    last_question = 0
    for position, message in enumerate(messages):
        if isinstance(message, HumanMessage):
            last_question = position

    input_tokens = 0
    output_tokens = 0
    for message in messages[last_question + 1 :]:
        if isinstance(message, AIMessage) and message.usage_metadata:
            input_tokens += message.usage_metadata["input_tokens"]
            output_tokens += message.usage_metadata["output_tokens"]
    return {"input_tokens": input_tokens, "output_tokens": output_tokens}
