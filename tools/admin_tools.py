from langchain.tools import ToolRuntime, tool

from config.clinic import clinic_time
from models.clinic_user import ClinicContext
from repositories import user_appointments
from tools.errors import ToolError


@tool
def get_all_bookings(runtime: ToolRuntime[ClinicContext]) -> dict:
    """List every booking at the clinic, for every patient. For the front desk (admins) only.

    Takes no arguments. Cancelled appointments are included and marked as cancelled.

    Examples:
    - "Show me all the bookings"
    - "Who is booked with Dr. Rao this week?"
    """
    # The role comes from the login, never from anything the user says in the chat.
    if runtime.context.user.profile.role != "admin":
        print(
            f"User {runtime.context.user.profile.full_name} ({runtime.context.user.profile.role}) tried to get all bookings."
        )
        raise ToolError(
            "I cannot assist you with this, I can only show you your own bookings. Please contact the front desk for help."
        )

    bookings = user_appointments.find_all_details()
    if not bookings:
        return {"status": "success", "message": "No bookings found.", "bookings": []}

    booking_list = []
    for b in bookings:
        booking_list.append(
            {
                "booking_code": b["booking_code"],
                "status": b["status"],
                "patient": b["patient_name"],
                "doctor": b["doctor_name"],
                "starts_at": clinic_time(b["starts_at"]),
                "reason": b["reason"],
            }
        )
    return {
        "status": "success",
        "message": f"{len(booking_list)} bookings found.",
        "bookings": booking_list,
    }
