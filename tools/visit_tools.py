from langchain.tools import ToolRuntime, tool

from config.clinic import clinic_time
from models.clinic_user import ClinicContext
from repositories import user_visits


@tool
def get_past_visits(runtime: ToolRuntime[ClinicContext]) -> str:
    """List all of the logged-in user's visits, most recently updated first.

    Takes no arguments. Use it when the user asks about their history with the clinic.

    Examples:
    - "When was I last here?"
    - "What did I come in for before?"
    """
    user = runtime.context.user.profile
    visits = user_visits.get_by_user(user.id)
    if not visits:
        return "No visits found."
    return "\n".join(
        f"Visit {v.id} (updated {clinic_time(v.updated_at)}): {v.summary}" for v in visits
    )


@tool
def get_past_visits_by_id(visit_id: int, runtime: ToolRuntime[ClinicContext]) -> str:
    """Get one of the logged-in user's visits by its visit ID.

    Use it when the user asks for the details of a specific visit. Visit IDs
    come from get_past_visits. It only finds visits that belong to the user.

    Examples:
    - "Tell me more about visit 3"
    - "What happened at my last visit?" (get the list first, then use the ID)

    Args:
        visit_id: The visit's ID number.
    """
    user = runtime.context.user.profile
    visit = user_visits.find_by_id(user.id, visit_id)
    if visit is None:
        return f"No visit with ID {visit_id} was found for this user."
    return f"Visit {visit.id} (updated {clinic_time(visit.updated_at)}): {visit.summary}"
