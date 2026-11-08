-- Clinic assistant schema. Safe to re-run: it drops everything first.
--
-- Every table has: id, created_at, created_by, updated_at, updated_by, void_sw.
-- A row with void_sw = true was a mistake and counts as deleted, so unique
-- rules are partial indexes that only look at rows where void_sw = false.

-- ---------------------------------------------------------------- drop
drop table if exists user_guardrail_events cascade;
drop table if exists user_chat_messages cascade;
drop table if exists user_chats         cascade;
drop table if exists sent_emails        cascade;
drop table if exists user_visits        cascade;
drop table if exists user_notes         cascade;
drop table if exists user_preferences   cascade;
drop table if exists user_facts         cascade;
drop table if exists user_intake        cascade;
drop table if exists user_appointments  cascade;
drop table if exists doctor_calendar    cascade;
drop table if exists doctors            cascade;
drop table if exists users              cascade;
drop table if exists insurance_plans    cascade;

drop function if exists set_updated_at() cascade;
drop sequence if exists booking_code_seq;

-- ---------------------------------------------------------------- shared
create function set_updated_at() returns trigger
language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

-- Booking codes look like APT-770460.
create sequence booking_code_seq start with 770460;

-- ---------------------------------------------------------------- users
-- created_by / updated_by are nullable only because the first user (the admin)
-- has to be inserted before any user id exists; setup.py then points his own
-- audit columns at himself.
create table users (
    id                  bigint generated always as identity primary key,
    role                text not null check (role in ('patient', 'admin')),
    full_name           text not null,
    email               text not null,
    phone               text,
    date_of_birth       date,
    insurance_plan_id   bigint,   -- foreign key added below (insurance_plans needs users first)
    insurance_member_id text,
    password_hash       text,
    created_at          timestamptz not null default now(),
    created_by          bigint references users (id),
    updated_at          timestamptz not null default now(),
    updated_by          bigint references users (id),
    void_sw             boolean not null default false,
    -- insurance and date of birth are patient-only
    constraint users_admin_has_no_patient_fields check (
        role <> 'admin'
        or (date_of_birth is null
            and insurance_plan_id is null
            and insurance_member_id is null)
    )
);
create unique index users_email_uq on users (email) where not void_sw;

-- ---------------------------------------------------------------- insurance_plans
create table insurance_plans (
    id          bigint generated always as identity primary key,
    code        text not null,
    name        text not null,
    accepted    boolean not null,
    created_at  timestamptz not null default now(),
    created_by  bigint not null references users (id),
    updated_at  timestamptz not null default now(),
    updated_by  bigint not null references users (id),
    void_sw     boolean not null default false
);
create unique index insurance_plans_code_uq on insurance_plans (code) where not void_sw;

alter table users
    add constraint users_insurance_plan_fk
    foreign key (insurance_plan_id) references insurance_plans (id);

-- ---------------------------------------------------------------- doctors
create table doctors (
    id              bigint generated always as identity primary key,
    full_name       text not null,
    speciality_code text not null,
    speciality      text not null,
    created_at      timestamptz not null default now(),
    created_by      bigint not null references users (id),
    updated_at      timestamptz not null default now(),
    updated_by      bigint not null references users (id),
    void_sw         boolean not null default false
);

-- ---------------------------------------------------------------- doctor_calendar
-- One row per 30-minute slot.
create table doctor_calendar (
    id          bigint generated always as identity primary key,
    doctor_id   bigint not null references doctors (id),
    starts_at   timestamptz not null,
    ends_at     timestamptz not null,
    status      text not null default 'open' check (status in ('open', 'booked', 'leave')),
    created_at  timestamptz not null default now(),
    created_by  bigint not null references users (id),
    updated_at  timestamptz not null default now(),
    updated_by  bigint not null references users (id),
    void_sw     boolean not null default false,
    check (ends_at > starts_at)
);
create unique index doctor_calendar_doctor_start_uq
    on doctor_calendar (doctor_id, starts_at) where not void_sw;

-- ---------------------------------------------------------------- user_appointments
create table user_appointments (
    id           bigint generated always as identity primary key,
    booking_code text not null default ('APT-' || nextval('booking_code_seq')),
    user_id      bigint not null references users (id),
    calendar_id  bigint not null references doctor_calendar (id),
    reason       text,
    status       text not null default 'booked' check (status in ('booked', 'cancelled')),
    created_at   timestamptz not null default now(),
    created_by   bigint not null references users (id),
    updated_at   timestamptz not null default now(),
    updated_by   bigint not null references users (id),
    void_sw      boolean not null default false
);
create unique index user_appointments_booking_code_uq
    on user_appointments (booking_code) where not void_sw;

-- ---------------------------------------------------------------- user_intake
-- One row per question and answer on an intake form. appointment_id stays
-- empty until the appointment is booked.
create table user_intake (
    id              bigint generated always as identity primary key,
    user_id         bigint not null references users (id),
    appointment_id  bigint references user_appointments (id),
    thread_id       text not null,
    question_key    text not null,
    question        text not null,
    answer          text not null,
    created_at      timestamptz not null default now(),
    created_by      bigint not null references users (id),
    updated_at      timestamptz not null default now(),
    updated_by      bigint not null references users (id),
    void_sw         boolean not null default false
);

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

-- ---------------------------------------------------------------- user_guardrail_events
-- One row for every emergency and every unsafe message the input judge catches.
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

-- ---------------------------------------------------------------- per-user memory
create table user_facts (
    id          bigint generated always as identity primary key,
    user_id     bigint not null references users (id),
    fact        text not null,
    created_at  timestamptz not null default now(),
    created_by  bigint not null references users (id),
    updated_at  timestamptz not null default now(),
    updated_by  bigint not null references users (id),
    void_sw     boolean not null default false
);

create table user_preferences (
    id          bigint generated always as identity primary key,
    user_id     bigint not null references users (id),
    preference  text not null,
    created_at  timestamptz not null default now(),
    created_by  bigint not null references users (id),
    updated_at  timestamptz not null default now(),
    updated_by  bigint not null references users (id),
    void_sw     boolean not null default false
);

create table user_notes (
    id          bigint generated always as identity primary key,
    user_id     bigint not null references users (id),
    note        text not null,
    created_at  timestamptz not null default now(),
    created_by  bigint not null references users (id),
    updated_at  timestamptz not null default now(),
    updated_by  bigint not null references users (id),
    void_sw     boolean not null default false
);

create table user_visits (
    id              bigint generated always as identity primary key,
    user_id         bigint not null references users (id),
    appointment_id  bigint not null references user_appointments (id),
    summary         text not null,
    created_at      timestamptz not null default now(),
    created_by      bigint not null references users (id),
    updated_at      timestamptz not null default now(),
    updated_by      bigint not null references users (id),
    void_sw         boolean not null default false
);

-- ---------------------------------------------------------------- sent_emails
create table sent_emails (
    id              bigint generated always as identity primary key,
    user_id         bigint not null references users (id),
    appointment_id  bigint references user_appointments (id),
    to_email        text not null,
    subject         text not null,
    body            text not null,
    created_at      timestamptz not null default now(),
    created_by      bigint not null references users (id),
    updated_at      timestamptz not null default now(),
    updated_by      bigint not null references users (id),
    void_sw         boolean not null default false
);

-- ---------------------------------------------------------------- updated_at triggers
create trigger users_set_updated_at             before update on users             for each row execute function set_updated_at();
create trigger insurance_plans_set_updated_at   before update on insurance_plans   for each row execute function set_updated_at();
create trigger doctors_set_updated_at           before update on doctors           for each row execute function set_updated_at();
create trigger doctor_calendar_set_updated_at   before update on doctor_calendar   for each row execute function set_updated_at();
create trigger user_appointments_set_updated_at before update on user_appointments for each row execute function set_updated_at();
create trigger user_intake_set_updated_at       before update on user_intake        for each row execute function set_updated_at();
create trigger user_facts_set_updated_at        before update on user_facts        for each row execute function set_updated_at();
create trigger user_preferences_set_updated_at  before update on user_preferences  for each row execute function set_updated_at();
create trigger user_notes_set_updated_at        before update on user_notes        for each row execute function set_updated_at();
create trigger user_visits_set_updated_at       before update on user_visits        for each row execute function set_updated_at();
create trigger sent_emails_set_updated_at       before update on sent_emails       for each row execute function set_updated_at();
