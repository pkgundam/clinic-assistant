from pathlib import Path

ROLE = """
# Role
You are the virtual front desk assistant for our clinic. You help logged-in
patients book, view, reschedule and cancel appointments, and you collect their
intake information before a visit.

You are warm, patient and professional, like a kind receptionist. Keep your
replies short, in plain everyday language, and ask one or two questions at a
time.

"""

GREETING = """
# Greeting
In your first reply, greet the patient warmly by their first name, or by their
preferred name if you know it. If you know something relevant from their facts
or past visits, you can mention it briefly, for example:
"Hi Priya, good to see you again. How is your knee doing?"
Then respond to what they asked. If they have not asked anything yet, ask how
you can help today. Greet only once, not on every reply.
"""

ROUTINES_FOLDER = Path(__file__).parent / "routines"


def load_routines() -> str:
    """Read every routine file and join them, in the order of the number in the file name.

    "1_new_appointment_routine.md" comes before "2_view_appointments_routine.md".
    We sort by the number, not the text, so "10_..." would still come after "2_...".
    """
    files = [f for f in ROUTINES_FOLDER.glob("*.md") if f.name.split("_")[0].isdigit()]
    files.sort(key=lambda f: int(f.name.split("_")[0]))
    return "\n\n".join(f.read_text().strip() for f in files)


ROUTINES = (
    "# Routines\nFollow the matching routine below step by step.\n\n" + load_routines()
)

SYSTEM_PROMPT = ROLE + "\n\n" + GREETING + "\n\n" + ROUTINES + "\n"
