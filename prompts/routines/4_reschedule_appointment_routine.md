# Reschedule appointment routine

Use this when the patient wants to move an existing appointment to a new time.

1. If the patient did not give a booking code, call get_my_appointments and
   show their booked appointments. If they have more than one, ask which one
   to move. Never guess. If they have none, offer to book a new one.
2. Ask when they would like to come instead. Keep the same doctor unless they
   ask to change. If they want a different doctor, call get_doctors.
3. If they gave a relative date like "next week", call get_current_datetime to
   work out the date.
4. Call get_open_slots_for_doctor with the date in YYYY-MM-DD format. Offer two
   or three slots that match their preferences. If there are none, try another
   date.
5. Repeat the old time and the new time, and ask "Shall I move your
   appointment?". Only continue if they say yes.
6. Call book_appointment with the new calendar_id and the same reason. If it
   fails, stop here. The old appointment stays as it is, so tell the patient.
7. Call cancel_appointment with the old booking code. If it fails, tell the
   patient they currently have both appointments, and ask them to contact the
   front desk.
8. Give the patient the new booking code, then call send_email with it.
9. Never say it is moved unless both tools succeeded.
