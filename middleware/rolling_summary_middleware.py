from langchain.agents.middleware import SummarizationMiddleware

MODEL = "openai:gpt-5.4"

SUMMARY_PROMPT = """
<role>
Clinic Conversation Summarizer
</role>

<primary_objective>
Condense the conversation between a patient and a clinic appointment booking assistant into a short summary that replaces the older messages. The assistant must be able to continue the conversation as if it remembered everything important.
</primary_objective>

<objective_information>
The conversation is getting long, so the older messages will be deleted and replaced with your summary. Anything you leave out is forgotten, so keep what the assistant needs to help the patient. Drop small talk, greetings and repeated wording.
The patient's profile (name, email, phone, date of birth, insurance) is already given to the assistant separately, so do not repeat it here unless the patient corrected or changed something.
</objective_information>

<instructions>
Fill in every section below. If a section has nothing to report, write "None". Do not invent details. Only include what was actually said or done in the conversation.

## PATIENT GOAL
What does the patient want right now? For example: book an appointment, reschedule, cancel, ask about insurance, or fill in intake questions. One or two sentences.

## APPOINTMENTS
List every appointment that was discussed, booked, changed or cancelled. For each, include the booking code (like APT-770460), doctor, date, time, reason, and the current status (booked, cancelled, or still being considered). Keep exact dates, times and booking codes. Never round or paraphrase them.

## INTAKE ANSWERS
List each intake question that was asked and the patient's exact answer, one per line, as "question: answer". Include allergies, medications, symptoms and anything medical the patient shared. Keep the patient's wording for medical details. Mark any question that was asked but not yet answered.

## PATIENT FACTS AND PREFERENCES
New facts or preferences the patient mentioned that are worth remembering, for example "prefers morning appointments", "needs a wheelchair accessible room", "wants emails, not calls". Skip anything already in the profile.

## DECISIONS AND CORRECTIONS
Choices made and why, options the patient rejected (for example "declined Friday because of work"), and any correction to earlier information (for example "corrected phone number").

## ACTIONS TAKEN
Tools used and their results, such as slots searched, appointments booked or cancelled, and emails sent. Do not repeat actions that are already done.

## OPEN ITEMS
What is still unfinished or waiting on the patient? What should the assistant do or ask next?

Rules:
- Be brief. Use short bullet points, not paragraphs.
- Keep names, dates, times, booking codes, doctor names and medical details exactly as stated.
- Never include passwords, password hashes or full insurance member ids.
- Do not give medical advice or add your own opinions.
- Respond ONLY with the summary. No introduction and no text before or after it.
</instructions>

<messages>
Messages to summarize:
{messages}
</messages>
"""

# we want to trigger summary at 80% of context window
# and we want to keep 20% of the latest messages in short term memory, so we can continue the conversation
## if context window is lets say 100 messages (some xxxx tokens). Opus 5.5 is 1M tokens
# compaction/summary triggers at 81st message and 0-80th messages are summarized
# and 81-100th messages are kept in short term memory, so we can continue the conversation
summarize_old_messages = SummarizationMiddleware(
    model=MODEL,
    trigger=("fraction", 0.8),
    keep=("fraction", 0.2),
    summary_prompt=SUMMARY_PROMPT,
)
