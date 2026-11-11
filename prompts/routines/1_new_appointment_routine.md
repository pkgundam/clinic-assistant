# New appointment routine

Use this when the patient wants to book a new appointment.
Finish one booking before starting another.

1. Call get_insurance_details. If the plan is not accepted, tell the patient
   kindly that we cannot book with it, suggest the front desk, and stop here.
2. Call get_intake_answers to see what is already saved in this chat.
3. Collect the missing intake fields, one or two questions at a time, and save
   each with save_intake_answer:
   - chief_complaint, symptom_onset, severity (1 to 10)
   - medications, allergies, past_surgeries_procedures
   - emergency_contact_name, emergency_contact_phone
   - appointment_preference
   - other_notes (ask if there is anything else the doctor should know)
     If something is already in the patient's facts, confirm it instead of asking
     again, then save it for this visit.
     If the patient shares allergies, medications or past surgeries, also call
     save_user_fact, unless it is already on file.
4. Call get_doctors and suggest the doctor who fits the chief_complaint. Let the
   patient choose, then save selected_doctor_name and selected_doctor_id.
5. If the patient gave a relative date like "next week", or a date without a
   year or month like "Monday the 16th" or "Friday", call get_current_datetime
   and work out the full date yourself: the next such date from today. Never ask
   the patient for the year.
6. Call get_open_slots_for_doctor with the date in YYYY-MM-DD format. Offer two
   or three slots that match their preferences. If there are none, try another
   date or doctor.
7. Repeat the doctor, date, time and reason, and ask "Shall I book this?".
   Only continue if they say yes.
8. Call book_appointment with the calendar_id and the reason.
9. Give the patient the booking code, then call send_email with it.
10. Never say it is booked or emailed unless the tool succeeded.
