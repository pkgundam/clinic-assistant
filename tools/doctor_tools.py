import re
from datetime import datetime, time, timedelta

from langchain.tools import ToolRuntime, tool

from config.clinic import CLINIC_TZ, clinic_time
from models.clinic_user import ClinicContext
from repositories import doctor_calendar, doctors, insurance_plans


@tool
def get_insurance_details(runtime: ToolRuntime[ClinicContext]) -> str:
    """Look up the logged-in user's insurance plan and whether the clinic accepts it.

    Takes no arguments. Use it when the user asks about their insurance or coverage.

    Examples:
    - "Do you take my insurance?"
    - "Which insurance plan do I have on file?"
    """
    profile = runtime.context.user.profile
    if profile.insurance_plan_id is None:
        return "The user has no insurance plan on file."

    plan = insurance_plans.find_by_id(profile.insurance_plan_id)
    if plan is None:
        return "The user's insurance plan could not be found."

    verdict = "accepts" if plan.accepted else "does NOT accept"
    return f"Insurance plan: {plan.name}. The clinic {verdict} this plan."


@tool
def get_doctors() -> str:
    """List all the doctors at the clinic with their ID and speciality.

    Takes no arguments. Use it to find the right doctor for the user's problem,
    and to get the doctor_id needed by get_open_slots_for_doctor.

    Examples:
    - "Who can look at my skin rash?"
    - "Which doctors do you have?"
    """
    all_doctors = doctors.get_all()
    return "\n".join(f"ID {d.id}: {d.full_name} ({d.speciality})" for d in all_doctors)


@tool
def get_open_slots_for_doctor(doctor_id: int, date: str) -> str:
    """Get a doctor's open appointment slots on one date. Past slots are never shown.

    Each slot has a calendar_id, which book_appointment needs.

    Examples:
    - doctor_id=2, date="2026-11-05"
    - "Does Dr. Rao have anything next Monday?" (work out the date with get_current_datetime first)

    Args:
        doctor_id: The doctor's ID from get_doctors.
        date: The day to check, in YYYY-MM-DD format only, e.g. 2026-11-05.
    """
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        return f"Invalid date '{date}'. The date must be in YYYY-MM-DD format, e.g. 2026-11-05."
    try:
        day = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return f"'{date}' is not a real calendar date. Use YYYY-MM-DD, e.g. 2026-11-05."

    doctor = doctors.find_by_id(doctor_id)
    if doctor is None:
        return f"No doctor with ID {doctor_id}."

    # The whole day in clinic time.
    day_start = datetime.combine(day, time.min, tzinfo=CLINIC_TZ)
    day_end = day_start + timedelta(days=1)

    slots = doctor_calendar.get_open_slots(doctor_id, day_start, day_end)
    if not slots:
        return f"{doctor.full_name} has no open slots on {date}."
    lines = [f"calendar_id {s.id}: {clinic_time(s.starts_at)}" for s in slots]
    return f"Open slots for {doctor.full_name} on {date}:\n" + "\n".join(lines)
