from dotenv import load_dotenv

# Must run before any project imports: the middleware builds a model at import
# time and needs OPENAI_API_KEY by then.
load_dotenv()

import secrets
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from repositories import user_chat_messages, user_chats
from services.auth import check_login, load_clinic_user
from services.chats import ask_and_save

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


# Plain `def` (not `async def`) because ask_and_save() is blocking: FastAPI runs these
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


def get_session(authorization: str | None) -> dict:
    """Return the session for the Authorization header, or raise 401."""
    # The header looks like: Authorization: Bearer <token>
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    session = sessions.get(token)
    if session is None:
        raise HTTPException(status_code=401, detail="Missing or unknown token")
    return session


@app.post("/chat")
def chat(body: ChatRequest, authorization: str | None = Header(default=None)):
    session = get_session(authorization)

    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # {"reply": "...", "tool_calls": [{"name", "args", "result"}, ...], "intent": "...", "judge_reason": "..."}
    return ask_and_save(message, session["clinic_user"], session["thread_id"])


@app.post("/chats")
def new_chat(authorization: str | None = Header(default=None)):
    """Start a new chat. The next /chat message goes into it."""
    session = get_session(authorization)

    # We don't save anything yet. The chat is saved with its first message,
    # so empty chats never show up in the list.
    session["thread_id"] = str(uuid4())
    return {"thread_id": session["thread_id"]}


@app.get("/chats")
def list_chats(authorization: str | None = Header(default=None)):
    """List the logged-in user's chats, most recent first."""
    session = get_session(authorization)
    user_id = session["clinic_user"].profile.id  # from the session, never from the request

    chats = []
    for saved_chat in user_chats.find_by_user(user_id):
        chats.append(
            {
                "thread_id": saved_chat.thread_id,
                "title": saved_chat.title,
                "updated_at": saved_chat.updated_at,
            }
        )
    return chats


@app.post("/chats/{thread_id}/open")
def open_chat(thread_id: str, authorization: str | None = Header(default=None)):
    """Open an old chat. The next /chat message carries on from where it left off."""
    session = get_session(authorization)
    user_id = session["clinic_user"].profile.id

    saved_chat = user_chats.find_by_thread(user_id, thread_id)
    if saved_chat is None:
        # Same answer for a chat that doesn't exist and a chat that is someone else's.
        raise HTTPException(status_code=404, detail="Chat not found")

    session["thread_id"] = saved_chat.thread_id

    messages = []
    for message in user_chat_messages.find_by_chat(saved_chat.id):
        messages.append(
            {
                "question": message.question,
                "ai_answer": message.ai_answer,
                "message_sent_at": message.message_sent_at,
            }
        )
    return {"thread_id": saved_chat.thread_id, "title": saved_chat.title, "messages": messages}
