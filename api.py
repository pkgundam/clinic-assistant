from dotenv import load_dotenv

# Must run before any project imports: the middleware builds a model at import
# time and needs OPENAI_API_KEY by then.
load_dotenv()

import secrets
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.clinic_agent import ask_with_tools
from services.auth import check_login, load_clinic_user

app = FastAPI(title="Clinic Assistant API")

# Only the web UI running on localhost:3000 may call this API from a browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logged-in sessions: token -> {"clinic_user": ClinicUser, "thread_id": str}.
# They only live in memory, so they are lost when the server restarts and
# everyone has to log in again. That is fine for now.
sessions: dict[str, dict] = {}


class LoginRequest(BaseModel):
    email: str
    password: str


class ChatRequest(BaseModel):
    message: str


# Plain `def` (not `async def`) because ask() is blocking: FastAPI runs these
# in a thread pool, so one slow answer does not freeze the whole server.
@app.post("/login")
def login(body: LoginRequest):
    user = check_login(body.email.strip(), body.password)
    if user is None:
        # Same message for a wrong email and a wrong password.
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = secrets.token_urlsafe(32)
    thread_id = str(uuid4())  # one thread per login, so the agent remembers the chat
    sessions[token] = {"clinic_user": load_clinic_user(user), "thread_id": thread_id}

    return {
        "token": token,
        "thread_id": thread_id,
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
        },
    }


@app.post("/chat")
def chat(body: ChatRequest, authorization: str | None = Header(default=None)):
    # The header looks like: Authorization: Bearer <token>
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    session = sessions.get(token)
    if session is None:
        raise HTTPException(status_code=401, detail="Missing or unknown token")

    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # {"reply": "...", "tool_calls": [{"name", "args", "result"}, ...]}
    return ask_with_tools(message, session["clinic_user"], session["thread_id"])
