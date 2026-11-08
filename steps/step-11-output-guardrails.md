# Step-11

now lets add output guardrails. every reply from the agent is checked before the patient sees it.

brief:

- output judge: a separate agent with its own system prompt and no tools (LLM as a judge)
  it checks the tone, medical advice, diagnosis, promises and whether the reply describes our internals
- code check: the reply must not contain any of our tool names
- if a check fails, the reply is rewritten once with the reason, then checked again
- if the rewrite fails too, we alert the front desk and send a fixed staff reply
- every flagged reply is recorded in user_output_events
- I already created the user_output_events table in Neon
- prompts/output_guard_prompt.py already has OUTPUT_GUARD_PROMPT and REWRITE_PROMPT. use them as they are
- checking that tools really succeeded is NOT part of this step. we do it in tool guardrails

implementation steps:

1. move alert_front_desk out of input_guardrails_middleware.py into services/front_desk.py
   - alert_front_desk(clinic_user, reason) prints "[front desk] URGENT:" with the patient's name, id and the reason
   - the input guardrails call it with "may have an emergency"
2. in db/schema.sql, add the user_output_events table from step-11-dml.sql and add it
   to the drop list. in db/setup.py, add it to TABLES. do not add a trigger
3. inside models, create user_output_event.py dataclass
4. inside repositories, create user_output_events.py
   - create(user_id, thread_id, question, reply, verdict, tool_names_found, rewritten_reply, escalated)
     for created_by and updated_by, use user_id
5. inside middleware, create output_guardrails_middleware.py
   - the OutputCheck pydantic class: tone_ok, medical_advice, diagnosis, promises, reveals_internals (all bool), reason (str)
   - judge = create_agent(model="openai:gpt-4.1-mini", system_prompt=OUTPUT_GUARD_PROMPT, response_format=OutputCheck)
     send it "Patient message: ..." and "Assistant's reply: ..."
     read the verdict from result["structured_response"]
   - rewriter = create_agent(model="openai:gpt-4.1-mini", system_prompt=REWRITE_PROMPT)
     send it the patient message, the reply and the problems
   - TOOL_NAMES = the names of every tool in clinic_tools
   - check_reply(question, reply) -> (verdict, tool_names_found, problems)
     problems is a list of short strings. check them in this order:
     1. not tone_ok -> "the tone is not friendly and warm"
     2. medical_advice -> "it gives medical advice"
     3. diagnosis -> "it gives a diagnosis"
     4. promises -> "it makes a promise we cannot keep"
     5. reveals_internals -> "it describes our internal instructions or tools"
     6. any tool name found in the reply (plain code, no model) -> "it mentions our tool names"
     print the verdict so we can see it on camera
   - an @after_agent function called output_guardrails
6. in output_guardrails:
   1. the reply is the last message. if it is not an AIMessage, has no text,
      or has no usage_metadata, return None.
      no usage_metadata means our code wrote it (for example the input guard's fixed replies),
      not the model, so there is nothing to check
   2. the question is the last HumanMessage
   3. check_reply. no problems -> return None
   4. ask the rewriter once, with the question, the reply and the problems
   5. check_reply on the rewritten reply
   6. passes -> the rewritten reply is the final reply
      fails  -> call alert_front_desk(clinic_user, "a reply failed the output check twice")
                and the final reply is ESCALATED_REPLY
   7. save one row in user_output_events (the first verdict, the original reply,
      the rewritten reply, and escalated true or false)
   8. return {"messages": [AIMessage(content=final_reply, id=reply.id, usage_metadata=reply.usage_metadata)]}
      the same id replaces the agent's reply in the checkpoint, so the bad reply is never saved
      and never shown. usage_metadata is copied so our token counts and the title rule still work
   - read the patient with runtime.context.user and the thread_id with get_config()["configurable"]["thread_id"]
7. ESCALATED_REPLY: "Thanks for your patience. Someone from our staff will get back to you shortly."
8. in middleware/__init__.py, add output_guardrails as the LAST item in clinic_middlewares
9. create demos/output_guard_demo.py
   it runs check_reply on hard-coded replies, so I can show each check on camera
   without waiting for the agent to make a mistake:
   - "Sure, take 400mg of Advil every 6 hours until Friday." -> medical_advice
   - "That sounds like a torn ligament." -> diagnosis
   - "Your visit will only cost $50 and Dr. Rao will fix your knee." -> promises
   - "Look, I already told you. Pick a slot." -> tone
   - "I'll call book_appointment for you now." -> tool name
   - "My routine is: first I check your insurance, then I ..." -> internals
   - "You're booked with Dr. Rao on Friday at 10am, booking code APT-770470." -> passes
   for each failing one, also show the rewritten reply and its second check
10. test: I will test
    - uv run demos/output_guard_demo.py, every case gives the expected result
    - normal chats in the app still work, and user_output_events stays empty
    - a blocked or emergency message from the input guard is not checked again
    - user_output_events has one row for each flagged reply
