from datetime import datetime
from zoneinfo import ZoneInfo

# The clinic works in this timezone. The database stores times in UTC.
CLINIC_TZ = ZoneInfo("America/Los_Angeles")


def clinic_time(moment: datetime) -> str:
    """Show a database time in clinic time, e.g. 'Thursday 2026-11-05 09:30 AM PST'."""
    return moment.astimezone(CLINIC_TZ).strftime("%A %Y-%m-%d %I:%M %p %Z")
