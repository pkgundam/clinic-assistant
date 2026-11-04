from langchain.tools import ToolRuntime, tool

from models.clinic_user import ClinicContext
from repositories import user_facts, user_notes, user_preferences

# Each save tool writes to the database AND adds the new row to the runtime
# context, so the next model call sees it in the system prompt.


@tool
def get_user_facts(runtime: ToolRuntime[ClinicContext]) -> str:
    """List the lasting health facts already saved for the logged-in user.

    Takes no arguments. Use it to check what is already known before saving
    something new, so we don't store the same fact twice.

    Examples:
    - "What allergies do I have on file?"
    - "What do you know about my health?"
    """
    facts = runtime.context.user.facts
    if not facts:
        return "No facts saved yet."
    return "\n".join(f"- {f.fact}" for f in facts)


@tool
def save_user_fact(fact: str, runtime: ToolRuntime[ClinicContext]) -> str:
    """Save a lasting health detail about the logged-in user.

    Use it when the user tells you something about their health that will stay
    true over time, like an allergy, a condition or a medication.
    Do not use it for scheduling likes and dislikes (use save_user_preference)
    or for other observations (use save_user_note).

    Examples:
    - "Allergic to penicillin"
    - "Has type 2 diabetes"

    Args:
        fact: The health detail, written as a short statement.
    """
    user = runtime.context.user
    user_id = user.profile.id
    user_fact = user_facts.create(user_id, fact)
    user.facts.append(user_fact)
    return f"Saved fact: {fact}"


@tool
def get_user_preferences(runtime: ToolRuntime[ClinicContext]) -> str:
    """List the preferences already saved for the logged-in user.

    Takes no arguments. Use it to check what is already known before saving
    something new, or when the user asks what you remember about how they
    like things done.

    Examples:
    - "What are my appointment preferences?"
    - "Do you remember when I like to come in?"
    """
    preferences = runtime.context.user.preferences
    if not preferences:
        return "No preferences saved yet."
    return "\n".join(f"- {p.preference}" for p in preferences)


@tool
def save_user_preference(preference: str, runtime: ToolRuntime[ClinicContext]) -> str:
    """Save how or when the logged-in user likes things done.

    Use it when the user says what they prefer, like a time of day, a doctor,
    or how they want to be contacted.

    Examples:
    - "Prefers morning appointments"
    - "Prefers email over phone calls"

    Args:
        preference: The preference, written as a short statement.
    """
    user = runtime.context.user
    user.preferences.append(user_preferences.create(user.profile.id, preference))
    return f"Saved preference: {preference}"


@tool
def get_user_notes(runtime: ToolRuntime[ClinicContext]) -> str:
    """List the other observations already saved about the logged-in user.

    Takes no arguments. Use it to check what is already known before saving
    something new, or when the user asks what notes you have about them.

    Examples:
    - "What notes do you have about me?"
    - "Is there anything the clinic should know about me?"
    """
    notes = runtime.context.user.notes
    if not notes:
        return "No notes saved yet."
    return "\n".join(f"- {n.note}" for n in notes)


@tool
def save_user_note(note: str, runtime: ToolRuntime[ClinicContext]) -> str:
    """Save another useful observation about the logged-in user.

    Use it for anything helpful that is not a lasting health fact and not a
    scheduling preference, like a worry or a communication need.

    Examples:
    - "Nervous about needles"
    - "Needs a wheelchair-accessible room"

    Args:
        note: The observation, written as a short statement.
    """
    user = runtime.context.user
    user.notes.append(user_notes.create(user.profile.id, note))
    return f"Saved note: {note}"
