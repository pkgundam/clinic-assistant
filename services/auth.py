from dataclasses import replace

import bcrypt

from models.clinic_user import ClinicUser
from models.user import User
from repositories import user_facts, user_notes, user_preferences
from repositories.users import find_by_email


def check_login(email: str, password: str) -> User | None:
    """Return the user if the email and password are right, otherwise None.

    A wrong email and a wrong password both give None, so callers can show the
    same "Invalid email or password" message for either.
    """
    user = find_by_email(email)
    if (
        user
        and user.password_hash
        and bcrypt.checkpw(password.encode(), user.password_hash.encode())
    ):
        return user
    return None


def load_clinic_user(user: User) -> ClinicUser:
    """Load the user's profile, facts, preferences and notes (once, after login)."""
    facts = user_facts.get_by_user(user.id)
    preferences = user_preferences.get_by_user(user.id)
    notes = user_notes.get_by_user(user.id)
    return ClinicUser(
        profile=replace(user, password_hash=None),  # the agent never sees the hash
        facts=facts,
        preferences=preferences,
        notes=notes,
    )
