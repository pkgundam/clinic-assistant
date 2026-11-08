-- ---------------------------------------------------------------- user_output_events
-- One row per agent reply that failed the output check.
create table user_output_events (
    id                  bigint generated always as identity primary key,
    user_id             bigint not null references users (id),
    thread_id           text not null,
    question            text not null,
    reply               text not null,
    tone_ok             boolean not null,
    medical_advice      boolean not null,
    diagnosis           boolean not null,
    promises            boolean not null,
    reveals_internals   boolean not null,
    tool_names_found    text,
    reason              text not null,
    rewritten_reply     text,
    escalated           boolean not null default false,
    created_at          timestamptz not null default now(),
    created_by          bigint not null references users (id),
    updated_at          timestamptz not null default now(),
    updated_by          bigint not null references users (id),
    void_sw             boolean not null default false
);
