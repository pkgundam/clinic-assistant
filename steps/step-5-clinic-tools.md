# Step-5

now that our agent has short-term and long-term memory
next, lets build the tools it needs to do the intake process

**1. utility_tools**

- `get_current_datetime`
  get the current date and time in clinic time, with the weekday.
  It is needed when a user says I want to book an appointment for next week

**2. visit_tools**

- `get_past_visits`
  get all visits of the logged in user from user_visits table order by updated_at desc
- `get_past_visits_by_id`
  get one visit by an ID. it must belong to the logged in user

**3. intake_tools**

- `save_intake_answer(question_key, question_text, user_answer)`
  The following are the intake fields
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
  look up by `user_id`, `thread_id`, `question_key` and `appointment_id is null`. Update if found, otherwise insert.
- `get_intake_answers`
  gets the answers saved so far in this chat, by `user_id`, `thread_id` and `appointment_id is null`.
  so the assistant can see what is still missing and does not ask again

**4. doctor_tools**

- `get_insurance_details()`
  the tool gets the insurance_id from logged in user profile and queries insurance_plans table.
- `get_doctors`
  gets all doctors from doctors table
- `get_open_slots_for_doctor(doctor_id, date)`
  gets future open slots for a doctor for given date from doctor_calendar table
  add a check and tool description to get the date in YYYY-MM-DD format (we will add such guardrails to all tools when we get to tool guardrails video)

**5. appointment_tools**

- `book_appointment(calendar_id, reason)`
  books the chosen calendar slot for the logged-in patient, with the reason for the visit, and returns the booking code.
  in one transaction:
  1. mark the slot booked, only if it is still open
  2. insert the appointment
  3. link this chat's intake rows to the appointment (by `user_id`, `thread_id`, `appointment_id is null`)
  4. call save_user_visit with a summary built from the doctor, slot time, reason and intake answers
- `get_my_appointments`
  gets all logged in user appointments with the doctor and slot time, order by slot time
- `cancel_appointment(booking_code)`
  cancels an existing appointment for a user and their booking code, and sets the slot back to open.
  so the tool must check that this booking_code actually belongs to the user first (Another tool guardrail)

**6. notification_tools**

- `send_email(booking_code)`
  sends the email out to the logged in user's email
  with the appointment details.
  fake email, we do not have an email server
  so just add print statements, and insert a row into sent_emails table.

All reads skip void rows (`not void_sw`).
