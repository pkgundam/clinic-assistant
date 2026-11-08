from datetime import datetime

from langchain.tools import tool

from config.clinic import CLINIC_TZ


@tool
def get_current_datetime() -> dict:
    """Get the current date and time in clinic time, with the weekday.

    Takes no arguments. Always call it before working out a relative date, because
    you do not know today's date on your own.

    Examples:
    - "I want to book an appointment for next week"
    - "Do you have anything tomorrow morning?"
    """
    now = datetime.now(CLINIC_TZ)
    return {
        "status": "success",
        "message": now.strftime(
            "Today is %A %Y-%m-%d, the time is %I:%M %p %Z (clinic time)."
        ),
        "date": now.strftime("%Y-%m-%d"),
    }
