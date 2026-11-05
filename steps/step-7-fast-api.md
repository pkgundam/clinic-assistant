Add a small FastAPI wrapper around the existing clinic agent, so a web UI can
use it instead of the terminal. Keep it simple and beginner friendly, since
this project is used in tutorial videos. Read CLAUDE.md first.

Install: uv add fastapi uvicorn

Create api.py in the project root. Run it with: uv run uvicorn api:app --reload

Endpoints:

1. POST /login
   Body: { "email": "...", "password": "..." }
   - Use find_by_email and bcrypt.checkpw, the same check as login() in chat.py.
   - Wrong email or password: return 401 with "Invalid email or password".
     Use the same message for both cases.
   - On success: build the ClinicUser (same as load_clinic_user in chat.py),
     create a thread_id with uuid4 and a token with secrets.token_urlsafe(32).
   - Keep sessions in a plain dict: token -> { clinic_user, thread_id }.
   - Return: { "token", "thread_id", "user": { "id", "full_name", "email", "role" } }

2. POST /chat
   Header: Authorization: Bearer <token>
   Body: { "message": "..." }
   - Unknown or missing token: return 401.
   - Empty message: return 400.
   - Call ask(message, clinic_user, thread_id) from agents/clinic_agent.py.
   - Return: { "reply": "..." }

Rules:

- Use plain `def` endpoints, not `async def`, because ask() is blocking.
- Use Pydantic models for the request bodies.
- Allow CORS from http://localhost:3000 only.
- Call load_dotenv() at the very top of api.py, before any project imports.
  Middleware builds a model at import time and needs OPENAI_API_KEY by then.
- Never return, print or log the password, password_hash or DATABASE_URL.
- Move login checking and load_clinic_user into one shared place so that
  chat.py and api.py both use it. chat.py must keep working as it does today.
- Do not change the agent, tools, middleware, prompts, repositories or database.
- No streaming, signup, logout or JWT for now.

Sessions are in memory, so they are lost when the server restarts. That is fine
for now. Add a short comment saying so.

When done, test it with curl:

1. Log in as priya@example.com with password clinicdemo.
2. Log in with a wrong password and confirm a 401.
3. Send "what is my name?" to /chat with the token.
4. Send a follow-up to confirm the agent remembers the conversation.
5. Call /chat without a token and confirm a 401.

Show me the results. Do not commit.

## update

Update POST /chat so the UI can show which tools the agent used.

New response:
{
"reply": "...",
"tool_calls": [
{ "name": "get_doctors", "args": { }, "result": "..." }
]
}

- ask() currently returns only the last message. Add what is needed to also get
  the tool calls, and keep chat.py working as it does today.
- result["messages"] holds the whole conversation. Only include tool calls from
  this turn, meaning the messages after the last HumanMessage.
- Match each AIMessage tool call to its ToolMessage using tool_call_id.
- If no tools were called, return an empty list.
- Do not change tools, middleware, prompts, repositories or the database.

Test with curl: "which doctors do you have?" should show get_doctors, and
"what is my name?" should return an empty list. Show me the results.
Do not commit.
