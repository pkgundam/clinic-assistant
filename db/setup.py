"""Create the clinic tables and load the starting data.

Run with:  uv run db/setup.py

Drops and recreates every table (see schema.sql), so it is safe to re-run.
The connection string comes from DATABASE_URL in .env and is never printed.
"""

import os
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import bcrypt
import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CLINIC_TZ = ZoneInfo("America/Los_Angeles")

TABLES = [
    "users",
    "insurance_plans",
    "doctors",
    "doctor_calendar",
    "user_appointments",
    "user_intake",
    "user_facts",
    "user_preferences",
    "user_notes",
    "user_visits",
    "sent_emails",
]

# Made-up password for the seeded patients, for demos only. Only its bcrypt hash is stored.
DEMO_PASSWORD = "clinicdemo"

ADMIN = {
    "full_name": "David",
    "email": "david@example.com",
    "phone": "555-0100",
}

INSURANCE_PLANS = [
    ("AETNA", "Aetna", True),
    ("BCBS", "Blue Cross Blue Shield", True),
    ("UHC", "UnitedHealthcare", True),
    ("CIGNA", "Cigna", False),
]

# full_name, email, phone, date_of_birth, plan code, member id
PATIENTS = [
    ("Priya", "priya@example.com", "555-0101", date(1990, 4, 12), "AETNA", "AET-100234"),
    ("Sachin", "sachin@example.com", "555-0102", date(1985, 9, 3), "BCBS", "BCB-200567"),
    ("Brian", "brian@example.com", "555-0103", date(1978, 1, 27), "UHC", "UHC-300891"),
]

# full_name, speciality_code, speciality
DOCTORS = [
    ("Dr. Anita Rao", "ORTHO", "Orthopedics"),
    ("Dr. James Carter", "GENMED", "General medicine"),
    ("Dr. Meera Iyer", "DERM", "Dermatology"),
    ("Dr. Sarah Lee", "CARDIO", "Cardiology"),
]

SLOT = timedelta(minutes=30)
# (start, end) of each block of the clinic day, clinic time
DAY_BLOCKS = [(time(9, 0), time(12, 0)), (time(13, 0), time(17, 0))]
CALENDAR_DAYS = 14


def hash_password(password: str) -> str:
    """Return a bcrypt hash (with its own random salt) as text."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def clinic_weekdays(today: date) -> list[date]:
    """Weekdays in the 14 days after `today` (tomorrow .. today + 14)."""
    days = (today + timedelta(days=n) for n in range(1, CALENDAR_DAYS + 1))
    return [d for d in days if d.weekday() < 5]


def slots_for(day: date):
    """Yield (starts_at, ends_at) as timezone-aware datetimes for one day."""
    for block_start, block_end in DAY_BLOCKS:
        start = datetime.combine(day, block_start, tzinfo=CLINIC_TZ)
        end_of_block = datetime.combine(day, block_end, tzinfo=CLINIC_TZ)
        while start < end_of_block:
            yield start, start + SLOT
            start += SLOT


def main() -> int:
    load_dotenv(ROOT / ".env")
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set. Add it to .env.", file=sys.stderr)
        return 1

    schema_sql = (ROOT / "db" / "schema.sql").read_text()
    today = datetime.now(CLINIC_TZ).date()
    weekdays = clinic_weekdays(today)

    # One transaction: either everything loads or nothing changes.
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute(schema_sql)

        # -- David, the admin. He is his own creator, so insert first and then
        #    point his audit columns at his own id.
        cur.execute(
            "insert into users (role, full_name, email, phone) "
            "values ('admin', %(full_name)s, %(email)s, %(phone)s)",
            ADMIN,
        )
        cur.execute(
            "update users set created_by = id, updated_by = id where email = %s",
            (ADMIN["email"],),
        )
        cur.execute("select id from users where email = %s", (ADMIN["email"],))
        david = cur.fetchone()[0]

        # -- Insurance plans
        cur.executemany(
            "insert into insurance_plans (code, name, accepted, created_by, updated_by) "
            "values (%s, %s, %s, %s, %s)",
            [(code, name, ok, david, david) for code, name, ok in INSURANCE_PLANS],
        )

        # -- Patients (plan looked up by code)
        cur.executemany(
            "insert into users (role, full_name, email, phone, date_of_birth, "
            "                   insurance_plan_id, insurance_member_id, password_hash, "
            "                   created_by, updated_by) "
            "select 'patient', %s, %s, %s, %s, p.id, %s, %s, %s, %s "
            "from insurance_plans p where p.code = %s",
            [
                (name, email, phone, dob, member, hash_password(DEMO_PASSWORD), david, david, plan)
                for name, email, phone, dob, plan, member in PATIENTS
            ],
        )

        # -- Doctors
        cur.executemany(
            "insert into doctors (full_name, speciality_code, speciality, created_by, updated_by) "
            "values (%s, %s, %s, %s, %s)",
            [(n, code, spec, david, david) for n, code, spec in DOCTORS],
        )
        cur.execute("select full_name, id from doctors")
        doctor_id = dict(cur.fetchall())

        # -- Calendar: every weekday, every doctor, 30-minute slots.
        #    Dr. Rao's first Friday is leave.
        first_friday = next(d for d in weekdays if d.weekday() == 4)
        rows = []
        for name, _, _ in DOCTORS:
            for day in weekdays:
                status = "leave" if name == "Dr. Anita Rao" and day == first_friday else "open"
                for starts_at, ends_at in slots_for(day):
                    rows.append((doctor_id[name], starts_at, ends_at, status, david, david))
        cur.executemany(
            "insert into doctor_calendar (doctor_id, starts_at, ends_at, status, created_by, updated_by) "
            "values (%s, %s, %s, %s, %s, %s)",
            rows,
        )

        # -- Appointments: look the patient and the slot up, mark the slot booked.
        appointments = [
            # patient email, doctor, day, slot start (clinic time), reason
            ("sachin@example.com", "Dr. James Carter", weekdays[1], time(10, 0), "annual checkup"),
            ("brian@example.com", "Dr. Meera Iyer", weekdays[2], time(14, 0), "skin rash"),
        ]
        for email, doctor, day, at, reason in appointments:
            starts_at = datetime.combine(day, at, tzinfo=CLINIC_TZ)
            cur.execute(
                "update doctor_calendar set status = 'booked', updated_by = %s "
                "where doctor_id = %s and starts_at = %s and status = 'open' and not void_sw "
                "returning id",
                (david, doctor_id[doctor], starts_at),
            )
            slot = cur.fetchone()
            if slot is None:
                raise RuntimeError(f"No open slot for {doctor} at {starts_at}")
            cur.execute(
                "insert into user_appointments (user_id, calendar_id, reason, created_by, updated_by) "
                "select u.id, %s, %s, %s, %s from users u where u.email = %s",
                (slot[0], reason, david, david, email),
            )

        # -- Row counts
        print(f"Calendar: {len(weekdays)} weekdays, {weekdays[0]} to {weekdays[-1]} (first Friday: {first_friday})")
        print(f"{'table':<20}rows")
        for table in TABLES:
            cur.execute(f"select count(*) from {table}")  # table names are the constants above
            print(f"{table:<20}{cur.fetchone()[0]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
