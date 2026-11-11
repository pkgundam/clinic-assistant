# Step-13

now lets add human in the loop. some actions are too important to let the agent do on its own,
so before it books an appointment or sends an email, it stops and asks the front desk first.

brief:

- first, remove the temporary override we added in the last video, so the input judge works again
- only two tools pause: book_appointment and send_email. everything else runs as before
- LangChain's built-in HumanInTheLoopMiddleware does the pause for us
- the front desk (David, our admin) decides. he has three choices:
  approve it, edit it (for example add a note to the email), or reject it with a reason
- while it waits, the patient sees "I've sent this to the front desk" and cannot send a new message in that chat
- the paused chat is saved in Postgres, so it can wait a minute or an hour, even across a restart
- every pause is saved as a row in a new table, user_approvals, so the front desk can see the list
- two new admin endpoints: one lists the waiting requests, one approves, edits or rejects a request.
  after the decision, the agent carries on from where it stopped
- the list shows the doctor and the time, not ids, so David can read it at a glance
- if something breaks after David decides, the request goes back on his list and he can click again
- I already created the user_approvals table in Neon (step-13-dml.sql)

implementation steps:

0. middleware/input_guardrails_middleware.py: delete the TEMPORARY block right after
   `verdict: InputCheck = result["structured_response"]` (the fake InputCheck with
   reason "TEMPORARY: judge result ignored"), so the judge's real verdict is used again.
   keep the "User's role: ..." line we added to the judge's message in the last step
   also in prompts/routines/1_new_appointment_routine.md step 5: a date with no year or month
   ("Monday the 16th", "Friday") is worked out from get_current_datetime too, never ask for the year
1. db: add the user_approvals table from step-13-dml.sql to db/schema.sql (after user_output_events)
   and add "drop table if exists user_approvals cascade;" at the top of the drop list.
   add "user_approvals" to TABLES in db/setup.py
2. models/user_approval.py: a UserApproval dataclass with the table's columns, like the other models
3. repositories/user_approvals.py:
   - create(user_id, thread_id, chat_message_id, tool_name, args) -> UserApproval
     args is a dict, store it with psycopg's Jsonb. created_by and updated_by = user_id (the patient)
   - find_by_id(approval_id) -> UserApproval | None (skip void rows)
   - find_pending() -> list of dicts: id, user_id, patient_name (users.full_name), tool_name,
     args, created_at of every pending approval, oldest first, skip void rows
   - is_waiting(thread_id) -> bool: true while the chat waits for the front desk, which is
     from the first pause until the final reply is saved. so: this thread has an approval
     whose chat message has no ai_answer yet. (a plain "status = 'pending'" check is not enough:
     it turns false while the agent is still running after the decision, so the patient UI
     would stop waiting too early)
   - decide(approval_id, status, edited_args, reject_reason, admin_id) -> bool
     sets status, edited_args (Jsonb or null), reject_reason, decided_by, decided_at = now(),
     updated_at = now(), updated_by = admin_id.
     only updates the row if it is still pending (where ... and status = 'pending'),
     returns True if a row was updated, so the same approval can never be decided twice
     (two clicks at the same moment too: only one update finds the row still pending)
   - reopen(approval_id): put it back to status 'pending' and clear edited_args, reject_reason,
     decided_by and decided_at. used when the agent fails to carry on after a decision
4. repositories/users.py: add find_by_id(user_id) -> User | None
   repositories/doctor_calendar.py: add find_slot_details(calendar_id) -> dict | None:
   the slot joined with its doctor: calendar_id, doctor_name, speciality, starts_at (skip void rows)
5. tools/notification_tools.py: send_email gets an optional note: str = ""
   - docstring: "note: leave empty. Only the front desk adds a note."
   - if note is not empty, add a line to the body: "Note from the clinic: {note}"
     this gives the admin something to edit, like "Please bring your knee X-ray."
   - move the subject into a small function email_subject(booking_code) -> "Your appointment {booking_code}"
     so the admin list can show the same subject before the email is sent
6. middleware/__init__.py: add the HITL middleware

   ```python
   human_in_the_loop = HumanInTheLoopMiddleware(
       interrupt_on={
           "book_appointment": {"allowed_decisions": ["approve", "edit", "reject"]},
           "send_email": {"allowed_decisions": ["approve", "edit", "reject"]},
       }
   )
   ```

   put it in clinic_middlewares after the limit middlewares and before output_guardrails
7. agents/clinic_agent.py:
   - one tool call at a time: build the model with
     init_chat_model("openai:gpt-5.4", model_kwargs={"parallel_tool_calls": False}).
     then every pause has exactly one action for the front desk
     (without it, "send me 3 emails" pauses with 3 actions and resuming with 1 decision fails)
   - one tool call per model call means more model calls, so in middleware/__init__.py raise
     ModelCallLimitMiddleware(run_limit=15) to run_limit=25. a patient who gives every intake
     answer in one message needs about 20
   - call agent.invoke(..., version="v2"). the result is then a GraphOutput:
     result.value is the state (messages, intent, ...) and result.interrupts is the list of pauses
   - move the code that builds the return dict out of ask() into
     build_result(result) -> dict, so ask() and resume() share it.
     it reads the messages and the state fields from result.value
   - if result.interrupts is not empty, the agent is paused:
     action = result.interrupts[0].value["action_requests"][0]
     return "paused": {"tool_name": action["name"], "args": action["args"]}
     and reply = PAUSED_REPLY:
     "I've sent this to the front desk for a quick check. I'll reply here as soon as they answer."
     rejected_response and new_response are None when paused (the output guard has not run yet)
     otherwise "paused": None
   - use result.value.get(...) for intent, judge_reason, rejected_response, new_response
   - add resume(decision: dict, clinic_user, thread_id) -> dict:
     agent.invoke(Command(resume={"decisions": [decision]}), same config and context as ask(),
     version="v2"), then return build_result(result)
8. services/chats.py, in ask_and_save:
   - right after redact: if user_approvals.is_waiting(thread_id), return the reply
     "We're still waiting on the front desk. I'll reply here as soon as they answer."
     with "waiting_for_approval": True, and do not save it or call the agent.
     a paused chat has a tool call with no result yet, and OpenAI errors if we send a new message on top of it
   - after ask(): if result["paused"], create the user_approvals row
     (with message.id as chat_message_id) and do not call save_answer yet,
     ai_answer stays empty until the front desk decides
   - also return "waiting_for_approval": True / False
9. services/approvals.py:
   - approval_details(user_id, tool_name, args) -> dict | None: what David needs to read the request.
     times are shown with clinic_time(...), the same as the tools
     - book_appointment: doctor_calendar.find_slot_details(args["calendar_id"]) ->
       {"doctor_name", "speciality", "starts_at", "starts_at_display", "reason" (from args)}
     - send_email: user_appointments.find_details_by_booking_code(user_id, booking_code) ->
       {"booking_code", "doctor_name", "speciality", "starts_at", "starts_at_display", "reason",
       "subject": email_subject(booking_code)}
     - None if the slot or booking code matches nothing
   - list_pending() -> list of dicts: id, patient_name, tool_name, args, details, created_at.
     args stays exactly as the agent wrote it (an edit starts from it), details is only for reading
   decide_approval(approval_id, decision, args, reason, admin) -> dict
   - three small exceptions: ApprovalNotFound, AlreadyDecided and ResumeFailed
     (the API turns them into 404, 409 and 502)
   - load the approval, ApprovalNotFound if missing
   - build the LangChain decision:
     - "approve" -> {"type": "approve"}
     - "edit" -> {"type": "edit", "edited_action": {"name": approval.tool_name, "args": {**approval.args, **args}}}
       the admin only sends the fields he changes, the rest keep the agent's values
     - "reject" -> {"type": "reject", "message": f"The clinic's front desk did not approve this. Their reason: {reason}"}
       LangChain shows it to the model as "User rejected the tool call ... with reason: ...",
       so we say it was the front desk, not the patient
   - user_approvals.decide(...) first, with status approved / edited / rejected.
     if it returns False, it was already decided: raise AlreadyDecided
   - load the patient: users.find_by_id(approval.user_id), then load_clinic_user(...)
     the agent must run as the patient, not as David
   - result = resume(decision, patient, approval.thread_id), inside try/except Exception:
     if it fails (for example OpenAI is down), print the error, user_approvals.reopen(approval.id)
     and raise ResumeFailed. the paused chat is still saved in Postgres at the pause,
     so the next click resumes it again
   - if result["paused"] again (send_email after the booking): create a new approval row
     with the same thread_id and chat_message_id
   - otherwise user_chat_messages.save_answer(approval.chat_message_id, reply, tokens, admin.id)
   - return {"reply": ..., "waiting_for_approval": ...}
10. api.py:
    - get_admin_session(authorization): get_session, then 403 if the role is not "admin"
      the role comes from the login, never from the request
    - GET /admin/approvals -> list_pending():
      id, patient_name, tool_name, args, details, created_at
    - POST /admin/approvals/{approval_id}/decide
      body: {"decision": "approve" | "edit" | "reject", "args": {...} or null, "reason": "..." or null}
      edit needs args, reject needs reason, otherwise 400. not found -> 404, already decided -> 409,
      ResumeFailed -> 502 "The assistant could not carry on. Please try again."
    - GET /chats/{thread_id}/messages: the same messages as open_chat (only the user's own chat),
      plus "waiting_for_approval". it does not switch the session's chat.
      the patient UI polls this while it is waiting
    - /chat and open_chat also return "waiting_for_approval"
    - CORS: also allow http://localhost:3500 (the web UI runs there)
11. chat.py needs no change: it prints the reply, which is the "sent to the front desk" message.
    the CLI has no admin, so the decision is made through the API
12. test: I will test
    - log in as priya, book with Dr. Rao -> the reply says it went to the front desk,
      a pending row in user_approvals, no booking yet
    - priya sends another message -> "still waiting on the front desk", the agent is not called
    - priya calls GET /admin/approvals -> 403
    - log in as david, GET /admin/approvals -> priya's book_appointment with its args
    - david approves -> the booking runs, then a new pending row for send_email
    - david edits send_email with note "Please bring your knee X-ray." -> the fake email
      has the note, and priya's chat gets the final reply
    - the admin list shows the doctor, the time and the reason for book_appointment,
      and the doctor, the time and the subject for send_email
    - david decides the same approval twice -> 409, also with two clicks at the same moment
    - make the resume fail once (in a throwaway script, not in the code) -> 502,
      the row is pending again, the next click works and priya gets her reply
    - book again, david rejects with "Dr. Rao is on leave on Friday" -> no booking,
      the reply tells priya why and offers another day
