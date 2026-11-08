class ToolError(Exception):
    """Raised by a tool when it cannot do what was asked.

    The message is written for the model, so it knows what to tell the patient.
    """
