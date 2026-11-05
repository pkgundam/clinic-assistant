# Step-9

now that every chat is saved, lets add a new chat option, list the existing chats
and let the user open an old chat and carry on from where they left off.

brief:

- add an API to start a new chat
- add an API to list the logged in user's chats
- add an API to open an old chat

implementation details:

1. in repositories/user_chats.py, add find_by_user(user_id) -> list[UserChat]
   - only this user's chats, skip void rows, order by updated_at desc
2. in repositories/user_chats.py, add find_by_thread(user_id, thread_id) -> UserChat or None
   it looks up by both user_id and thread_id and skips void rows,
   so another patient's chat comes back as None
3. in repositories/user_chat_messages.py, add find_by_chat(chat_id) -> list[UserChatMessage]
   skip void rows, order by message_sent_at, then id
4. in api.py, move the token check out of /chat into a helper get_session(authorization)
   that returns the session or raises 401. all endpoints use it
5. in api.py, add POST /chats
   - create a new thread_id with uuid4 and store it in session["thread_id"]
   - return {"thread_id": ...}
   - do not insert into user_chats here. the row is created on the first message,
     so empty chats never show up in the list
6. in api.py, add GET /chats
   - take the user_id from the session, never from the request
   - return a list of {"thread_id", "title", "updated_at"}
7. in api.py, add POST /chats/{thread_id}/open
   - call find_by_thread with the user_id from the session
   - if it returns None, raise 404 "Chat not found"
     (same answer for a chat that does not exist and a chat that belongs to someone else)
   - store the thread_id in session["thread_id"], so the next /chat continues this chat
   - return {"thread_id", "title", "messages": [{"question", "ai_answer", "message_sent_at"}, ...]}
   - messages come from user_chat_messages, not from the checkpoint tables
8. /login and /chat keep working as they do today. do not change chat.py,
   every terminal run already starts a new chat
9. test: I will test with curl
    - log in as priya, send a message, GET /chats shows 1 chat with a title
    - POST /chats, send another message, GET /chats shows 2 chats, newest first
    - POST /chats without sending a message, GET /chats still shows 2 chats
    - open the first chat, the messages come back in order
    - send a message in it, the agent remembers the earlier conversation
    - restart the API, log in, open the chat, the agent still remembers
    - log in as sachin, GET /chats does not show priya's chats
    - as sachin, open priya's thread_id, it returns 404

Give me the 3 CURL commands when the implementation is done.
