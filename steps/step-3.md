Step-3
now that we have the user profile from the database,
lets give the agent short term memory for the conversation.
brief:

- define a thread_id
- add an inmemory checkpointer
- add user to agent's context
- update system_prompt to include user_profile using @dynamic_prompt middleware

1. in chat.py, after login, create a thread_id with uuid4 (one per chat session).
   pass the user and the thread_id to the ask() method
2. in clinic_agent.py, add an in-memory checkpointer (InMemorySaver) to the agent.
   we will move it to postgres later.
3. define a context_schema for the agent that holds the user.
   pass the user as context, and the thread_id as the memory config, when invoking the agent
4. create a folder called middleware
   inside it create user_profile_middleware.py with a @dynamic_prompt function
   that adds the user's details to the system prompt inside <user_profile></user_profile>
   (name, email, phone, date of birth, insurance. NOT the password hash)
   print the final system prompt to see it
5. create an **init**.py inside the middle and then export clinic_middlewares = [], this will contain all the middlewares we create
6. test: log in as priya, ask "what is my name?"
