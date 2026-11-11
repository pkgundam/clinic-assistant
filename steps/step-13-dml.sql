-- One row every time the agent pauses before book_appointment or send_email.
-- The front desk approves, edits or rejects it.
create table user_approvals (
    id               bigint generated always as identity primary key,
    user_id          bigint not null references users (id),
    thread_id        text not null,
    chat_message_id  bigint not null references user_chat_messages (id),
    tool_name        text not null,
    args             jsonb not null,
    status           text not null default 'pending'
                     check (status in ('pending', 'approved', 'edited', 'rejected')),
    edited_args      jsonb,
    reject_reason    text,
    decided_by       bigint references users (id),
    decided_at       timestamptz,
    created_at       timestamptz not null default now(),
    created_by       bigint not null references users (id),
    updated_at       timestamptz not null default now(),
    updated_by       bigint not null references users (id),
    void_sw          boolean not null default false
);
