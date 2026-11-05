# Step-7

now that the user_chats and user_chat_messages tables exist,
lets move the conversation history to postgres and save every chat.

brief:

- replace InMemorySaver with PostgresSaver so conversations survive a restart
- save one user_chats row per chat
- save one user_chat_messages row per turn (question, answer, timings, tokens)
- generate the chat title with the LLM after the first answer
- every update statement must set updated_at = now() and updated_by
- the new tables are already created

implementation steps:

1. install langgraph-checkpoint-postgres using uv
2. in config/database.py, add a second connection called checkpoint_conn
   (same settings as conn: autocommit=True, row_factory=dict_row)
   the checkpointer gets its own connection so it never writes inside
   the transactions that book_appointment and cancel_appointment open on conn
3. in clinic_agent.py, replace InMemorySaver with PostgresSaver(checkpoint_conn)
   call checkpointer.setup() once, it creates the checkpoint tables
4. inside models, create user_chat.py and user_chat_message.py dataclasses
5. inside repositories, create user_chats.py
   - save(user_id, thread_id) -> returns a UserChat
     insert the row. if the thread already exists, only refresh updated_at and updated_by:
     on conflict (thread_id) where not void_sw do update set updated_at = now(), updated_by = excluded.updated_by
   - save_title(chat_id, title, user_id)
6. inside repositories, create user_chat_messages.py
   - create(chat_id, question, user_id) -> returns a UserChatMessage
   - save_answer(message_id, ai_answer, input_tokens, output_tokens, user_id)
     also sets response_recvd_at = now()
7. inside util, create token_usage.py with get_token_usage(messages)
   result["messages"] holds the whole conversation, so only count this turn:
   add up usage_metadata on the AI messages after the last human message
   return input_tokens and output_tokens
   update ask_with_tools to include them in the dict it returns
8. inside services, create chats.py
   - generate_title(question): a short LLM call that returns a title of 3 to 6 words
   - ask_and_save(question, clinic_user, thread_id), in this order:
     1. user_chats.save
     2. user_chat_messages.create (the question is saved before the model call,
        so it is kept even if the model call fails)
     3. ask_with_tools
     4. user_chat_messages.save_answer
     5. if the chat has no title yet, generate_title and save_title
        returns {"reply": ..., "tool_calls": [...]}
9. update chat.py and api.py to call ask_and_save
   the /chat response must stay the same: reply and tool_calls
   remove ask() from clinic_agent.py if nothing uses it anymore
10. test: I will test it by logging in as priya and asking 2 questions
    - user_chats has 1 row with a title
    - user_chat_messages has 2 rows with answers and token counts
    - the checkpoint tables exist
