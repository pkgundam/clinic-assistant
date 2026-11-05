-- ---------------------------------------------------------------- user_chats
-- One row per chat. thread_id links it to the PostgresSaver checkpoints.
-- title stays empty until the LLM generates it.
create table user_chats (
    id          bigint generated always as identity primary key,
    user_id     bigint not null references users (id),
    thread_id   text not null,
    title       text,
    created_at  timestamptz not null default now(),
    created_by  bigint not null references users (id),
    updated_at  timestamptz not null default now(),
    updated_by  bigint not null references users (id),
    void_sw     boolean not null default false
);
create unique index user_chats_thread_id_uq on user_chats (thread_id) where not void_sw;

-- ---------------------------------------------------------------- user_chat_messages
-- One row per turn: the question, then the answer once it arrives.
create table user_chat_messages (
    id                  bigint generated always as identity primary key,
    chat_id             bigint not null references user_chats (id),
    question            text not null,
    ai_answer           text,
    message_sent_at     timestamptz not null default now(),
    response_recvd_at   timestamptz,
    input_tokens        integer,
    output_tokens       integer,
    created_at          timestamptz not null default now(),
    created_by          bigint not null references users (id),
    updated_at          timestamptz not null default now(),
    updated_by          bigint not null references users (id),
    void_sw             boolean not null default false
);
