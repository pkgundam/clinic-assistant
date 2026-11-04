# Cancel appointment routine

Use this when the patient wants to cancel an appointment.

1. If the patient did not give a booking code, call get_my_appointments and
   show their booked appointments with the doctor, date, time and booking code.
   If they have none, tell them so and stop here.
2. If they have more than one, ask which one they want to cancel. Never guess.
3. Repeat the doctor, date and time, and ask "Are you sure you want to cancel
   this appointment?". Only continue if they say yes.
4. Call cancel_appointment with the booking code.
5. If it succeeded, confirm the cancellation and ask if they would like to book
   a new time. If it failed, tell the patient what went wrong.
6. Never say it is cancelled unless the tool succeeded.
