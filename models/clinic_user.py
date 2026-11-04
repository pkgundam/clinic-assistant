from dataclasses import dataclass, field

from models.user import User
from models.user_fact import UserFact
from models.user_note import UserNote
from models.user_preference import UserPreference


@dataclass
class ClinicUser:
    """Everything the agent knows about the logged-in user.

    Loaded once at login. The memory tools add to these lists when something
    new is saved, so the system prompt always shows the latest details.
    """

    profile: User  # the user row, with password_hash set to None
    facts: list[UserFact] = field(default_factory=list)
    preferences: list[UserPreference] = field(default_factory=list)
    notes: list[UserNote] = field(default_factory=list)


@dataclass
class ClinicContext:
    """Extra information passed to the agent on every call."""

    user: ClinicUser
