# Clinic Assistant

A friendly clinic appointment booking assistant built with LangChain.

## Tech stack
- Python 3.12+, managed with `uv`
- LangChain (`create_agent`) with OpenAI `gpt-5.4`
- Neon Postgres database (schema and seed data in `db/`)

## Project layout
- `agents/clinic_agent.py` - the agent and the `ask()` function
- `prompts/prompts.py` - the system prompt
- `chat.py` - command-line chat wrapper around the agent
- `db/` - database schema, seed script and example queries
- `steps/` - step-by-step build instructions

## Commands
- Install packages: `uv add <package>`
- Run the chat: `uv run chat.py`
- Set up the database: `uv run db/setup.py`

## Rules
- Keep the code simple and beginner friendly. This project is used in tutorial videos.
- API keys live in `.env` (never commit it). `.env.example` shows the names.
- Use `uv` for everything, not `pip`.
