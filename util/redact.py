import re

SSN_PATTERN = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")


def redact(text: str) -> str:
    """Replace any social security number in the text with [REDACTED SSN]."""
    return SSN_PATTERN.sub("[REDACTED SSN]", text)
