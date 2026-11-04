from langchain.tools import ToolRuntime, tool

from models.clinic_user import ClinicContext
from repositories import user_intake

# The questions we collect before booking.
INTAKE_KEYS = [
    "chief_complaint",
    "symptom_onset",
    "severity",
    "medications",
    "allergies",
    "past_surgeries_procedures",
    "emergency_contact_name",
    "emergency_contact_phone",
    "appointment_preference",
    "selected_doctor_name",
    "selected_doctor_id",
    "other_notes",
]


@tool
def save_intake_answer(
    question_key: str, question_text: str, user_answer: str, runtime: ToolRuntime[ClinicContext]
) -> str:
    """Save the user's answer to one intake question for this chat.

    Call it each time the user answers an intake question. Saving the same
    question_key again replaces the earlier answer.

    The valid question_key values are: chief_complaint, symptom_onset, severity,
    medications, allergies, past_surgeries_procedures, emergency_contact_name,
    emergency_contact_phone, appointment_preference, selected_doctor_name,
    selected_doctor_id, other_notes.

    Examples:
    - question_key="allergies", question_text="Do you have any allergies?", user_answer="Penicillin"
    - question_key="severity", question_text="How severe is the pain from 1 to 10?", user_answer="6"

    Args:
        question_key: One of the valid keys listed above.
        question_text: The question that was asked.
        user_answer: What the user answered.
    """
    if question_key not in INTAKE_KEYS:
        return f"Invalid question_key '{question_key}'. Use one of: {', '.join(INTAKE_KEYS)}."

    user = runtime.context.user.profile
    thread_id = runtime.config["configurable"]["thread_id"]
    user_intake.save(user.id, thread_id, question_key, question_text, user_answer)
    return f"Saved {question_key}: {user_answer}"


@tool
def get_intake_answers(runtime: ToolRuntime[ClinicContext]) -> str:
    """Get the intake answers saved so far in this chat, and which ones are still missing.

    Takes no arguments. Use it to see what is left to ask, so you never ask the
    same question twice.

    Examples:
    - Before asking the next intake question
    - Before booking, to check nothing important is missing
    """
    user = runtime.context.user.profile
    thread_id = runtime.config["configurable"]["thread_id"]
    answers = user_intake.get_open(user.id, thread_id)

    saved = "\n".join(f"- {a.question_key}: {a.answer}" for a in answers) or "(nothing yet)"
    answered_keys = {a.question_key for a in answers}
    missing = [key for key in INTAKE_KEYS if key not in answered_keys]
    return f"Answers so far:\n{saved}\n\nStill missing: {', '.join(missing) or 'nothing'}"
