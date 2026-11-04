# View appointments routine

Use this when the patient asks about their appointments, for example
"when is my appointment?" or "do I have anything booked?".

1. Call get_my_appointments.
2. If they have none, tell them so and ask if they would like to book one.
3. Show upcoming booked appointments first, with the doctor, date, time, reason
   and booking code. Times are in clinic time (Pacific).
4. Mention cancelled or past appointments only if the patient asks about them.
   If you need today's date to tell past from upcoming, call
   get_current_datetime.
5. Ask if they would like to change or cancel anything.
