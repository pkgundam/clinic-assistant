from tools.appointment_tools import (
    book_appointment,
    cancel_appointment,
    get_my_appointments,
)
from tools.doctor_tools import (
    get_doctors,
    get_insurance_details,
    get_open_slots_for_doctor,
)
from tools.intake_tools import get_intake_answers, save_intake_answer
from tools.memory_tools import (
    get_user_facts,
    get_user_notes,
    get_user_preferences,
    save_user_fact,
    save_user_note,
    save_user_preference,
)
from tools.notification_tools import send_email
from tools.utility_tools import get_current_datetime
from tools.visit_tools import get_past_visits, get_past_visits_by_id

# Every tool we create is added to this list and given to the agent.
clinic_tools = [
    # long-term memory
    get_user_facts,
    save_user_fact,
    get_user_preferences,
    save_user_preference,
    get_user_notes,
    save_user_note,
    # utility
    get_current_datetime,
    # visits
    get_past_visits,
    get_past_visits_by_id,
    # intake
    save_intake_answer,
    get_intake_answers,
    # doctors
    get_insurance_details,
    get_doctors,
    get_open_slots_for_doctor,
    # appointments
    book_appointment,
    get_my_appointments,
    cancel_appointment,
    # notifications
    send_email,
]
