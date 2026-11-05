# Step-4

now that our agent has short term memory,
lets give it long term memory.
lets build the tools it needs for it.

brief:

- create the remaining model data classes
- create the code to read from user facts, preferences and notes table and also write to it.
- create the tools for storing facts, preferences and notes
- load the facts, preferences and notes one time during login
- update the agent's runtime context to contain the user's profile, facts, preferences and notes.
- update the system prompt to include <user_facts>, <user_preferences> and <user_notes>. Initially this will be empty and when a new fact or a preference or notes get stored, the tool updates the runtime context accordingly so our dynamic_prompt middleware can rebuild the system prompt with updated details.
- I will test it and provide some facts, preferences and notes to see if they get saved in our database tables against my user_id

We will need the following tools implemented

1. `get_user_facts`
2. `save_user_fact`
3. `get_user_preferences`
4. `save_user_preference`
5. `get_user_notes`
6. `save_user_note`

implementation steps:

0. create the dataclasses for the other tables inside the "models" folder.
1. inside repositories, create these files with the respective save and get methods.
   user_facts.py -> create(user_id, fact)
   user_preferences.py -> create(user_id, preference)
   user_notes.py -> create(user_id, note)
   for created_by and updated_by, use logged in user_id
   this implementation will be insert only.
2. create a folder called tools
   inside it create insurance_tools.py with the get_insurance_details tool
   it takes no arguments. it looks up the plan of the logged in user and returns the plan name and whether it is accepted
3. inside tools, create memory_tools.py with the other three tools
   each one takes a single text argument and saves it for the logged in user
   - save_user_fact(fact) -> lasting health details. ex: "Allergic to penicillin"
   - save_user_preferences(preference) -> how or when they like things. ex: "Prefers morning appointments"
   - save_user_notes(note) -> other useful observations. ex: "Nervous about needles"
4. to know who is logged in, add a runtime: ToolRuntime parameter to each tool
   and read the user with runtime.context.user. the LLM never sees this parameter.
5. write a clear docstring for every tool with 1-2 examples. the docstring is what the LLM reads to decide when to call it.
6. create an **init**.py inside tools and export clinic_tools = [...] with all tools
   pass it to the agent in clinic_agent.py with tools=clinic_tools
7. finally once the login is successful, query the user_facts, user_preferences and user_notes for the user_id
   and retrieve them.
   create a new custom data class called ClinicUser and it will have four variables -- profile (user object minus the password hash), notes, preferences and facts
   pass this ClinicUser to the agent and use it for the agent context.
8. test: I will test it and say
   - "I am allergic to penicillin" -> check the user_facts table in Neon
   - "I prefer morning appointments" -> check user_preferences
   - "I am nervous about needles" -> check user_notes
