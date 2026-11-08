-- ---------------------------------------------------------------- user_guardrail_events
-- One row per message the input judge flagged: unsafe or an emergency.
create table user_guardrail_events (
    id              bigint generated always as identity primary key,
    user_id         bigint not null references users (id),
    thread_id       text not null,
    question        text not null,
    safe            boolean not null,
    injection_type  text not null,
    emergency       boolean not null,
    intent          text not null,
    reason          text not null,
    created_at      timestamptz not null default now(),
    created_by      bigint not null references users (id),
    updated_at      timestamptz not null default now(),
    updated_by      bigint not null references users (id),
    void_sw         boolean not null default false
);
