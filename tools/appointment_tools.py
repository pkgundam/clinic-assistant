from langchain.tools import ToolRuntime, tool

from config.clinic import clinic_time
from config.database import conn
from models.clinic_user import ClinicContext
from repositories import doctor_calendar, user_appointments, user_intake, user_visits


def save_user_visit(user_id: int, appointment: dict, reason: str) -> None:
    """Save a visit whose summary is built from the doctor, slot time, reason and intake answers."""
    answers = user_intake.get_by_appointment(appointment["id"])
    intake_text = "; ".join(f"{a.question_key}: {a.answer}" for a in answers) or "none"
    summary = (
        f"{appointment['doctor_name']} ({appointment['speciality']}) on "
        f"{clinic_time(appointment['starts_at'])}. Reason: {reason}. Intake: {intake_text}."
    )
    user_visits.create(user_id, appointment["id"], summary)


@tool
def book_appointment(calendar_id: int, reason: str, runtime: ToolRuntime[ClinicContext]) -> str:
    """Book a calendar slot for the logged-in user and return the booking code.

    Only call it after the user has chosen a slot (calendar_id comes from
    get_open_slots_for_doctor) and you have collected the intake answers.
    It fails if the slot was taken in the meantime.

    Examples:
    - calendar_id=412, reason="Knee pain after a fall"
    - calendar_id=87, reason="Skin rash on both arms"

    Args:
        calendar_id: The slot's calendar_id.
        reason: Why the user is visiting, in a short sentence.
    """
    user = runtime.context.user.profile
    thread_id = runtime.config["configurable"]["thread_id"]

    # All four steps happen together, or none of them do.
    with conn.transaction():
        # 1. mark the slot booked, only if it is still open
        slot = doctor_calendar.book_if_open(calendar_id, user.id)
        if slot is None:
            return f"Slot {calendar_id} is not available. Ask the user to pick another slot."

        # 2. insert the appointment
        appointment = user_appointments.create(user.id, calendar_id, reason)

        # 3. link this chat's intake answers to the appointment
        user_intake.link_to_appointment(user.id, thread_id, appointment.id)

        # 4. save a visit with a summary of the booking
        details = user_appointments.find_details_by_booking_code(user.id, appointment.booking_code)
        save_user_visit(user.id, details, reason)

    return (
        f"Booked! Booking code {appointment.booking_code} with {details['doctor_name']} "
        f"on {clinic_time(details['starts_at'])}."
    )


@tool
def get_my_appointments(runtime: ToolRuntime[ClinicContext]) -> str:
    """List all of the logged-in user's appointments with the doctor and time, ordered by time.

    Takes no arguments. Cancelled appointments are included and marked as cancelled.

    Examples:
    - "What appointments do I have?"
    - "When is my next visit?"
    """
    user = runtime.context.user.profile
    appointments = user_appointments.get_details_by_user(user.id)
    if not appointments:
        return "No appointments found."
    return "\n".join(
        f"{a['booking_code']} [{a['status']}]: {a['doctor_name']} ({a['speciality']}) "
        f"on {clinic_time(a['starts_at'])}. Reason: {a['reason']}"
        for a in appointments
    )


@tool
def cancel_appointment(booking_code: str, runtime: ToolRuntime[ClinicContext]) -> str:
    """Cancel one of the logged-in user's appointments by its booking code and free the slot.

    Only works on appointments that belong to the user. Confirm with the user before cancelling.

    Examples:
    - booking_code="APT-770460"
    - "Please cancel my appointment on Friday" (find the code with get_my_appointments first)

    Args:
        booking_code: The booking code, like APT-770460.
    """
    user = runtime.context.user.profile
    appointment = user_appointments.find_details_by_booking_code(
        user.id, booking_code.strip().upper()
    )
    # Guardrail: a code that is not this user's looks exactly like a code that doesn't exist.
    if appointment is None:
        return f"No appointment with booking code {booking_code} was found for this user."
    if appointment["status"] == "cancelled":
        return f"Appointment {appointment['booking_code']} is already cancelled."

    with conn.transaction():
        user_appointments.cancel(appointment["id"], user.id)
        doctor_calendar.set_open(appointment["calendar_id"], user.id)

    return f"Cancelled appointment {appointment['booking_code']}. The slot is open again."
