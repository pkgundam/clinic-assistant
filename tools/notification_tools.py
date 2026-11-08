from langchain.tools import ToolRuntime, tool

from config.clinic import clinic_time
from models.clinic_user import ClinicContext
from repositories import sent_emails, user_appointments
from tools.errors import ToolError


@tool
def send_email(booking_code: str, runtime: ToolRuntime[ClinicContext]) -> dict:
    """Email the appointment details to the logged-in user.

    Use it after booking, or when the user asks for their appointment details by email.
    It only works on appointments that belong to the user.

    Examples:
    - booking_code="APT-770460"
    - "Can you email me the confirmation?"

    Args:
        booking_code: The booking code, like APT-770460.
    """
    user = runtime.context.user.profile
    appointment = user_appointments.find_details_by_booking_code(
        user.id, booking_code.strip().upper()
    )
    if appointment is None:
        raise ToolError(
            f"No appointment with booking code {booking_code} was found for this user."
        )

    subject = f"Your appointment {appointment['booking_code']}"
    body = (
        f"Hi {user.full_name},\n\n"
        f"Your appointment is {appointment['status']}.\n"
        f"Booking code: {appointment['booking_code']}\n"
        f"Doctor: {appointment['doctor_name']} ({appointment['speciality']})\n"
        f"When: {clinic_time(appointment['starts_at'])}\n"
        f"Reason: {appointment['reason']}\n"
    )

    # We have no email server, so we only print the email and store it.
    print(
        f"\n--- FAKE EMAIL to {user.email} ---\nSubject: {subject}\n\n{body}---------------------"
    )
    sent_emails.create(user.id, appointment["id"], user.email, subject, body)
    return {
        "status": "success",
        "message": f"Email sent to {user.email}.",
        "to": user.email,
    }
