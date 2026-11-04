from langchain.agents.middleware import ModelRequest, dynamic_prompt


@dynamic_prompt
def user_profile_middleware(request: ModelRequest) -> str:
    """Build the system prompt from what we know about the logged-in user.

    Runs before every model call. The memory tools update the ClinicUser in the
    context after saving, so the next call already sees the new details.
    """
    user = request.runtime.context.user  # the ClinicUser

    # 1. user profile (never includes the password hash)
    profile = user.profile
    user_profile = (
        "<user_profile>\n"
        f"Name: {profile.full_name}\n"
        f"Email: {profile.email}\n"
        f"Phone: {profile.phone}\n"
        f"Date of birth: {profile.date_of_birth}\n"
        f"Insurance plan id: {profile.insurance_plan_id}\n"
        f"Insurance member id: {profile.insurance_member_id}\n"
        "</user_profile>"
    )

    # 2. user facts
    facts = "\n".join(f"- {fact.fact}" for fact in user.facts)
    user_facts = f"<user_facts>\n{facts}\n</user_facts>"

    # 3. user preferences
    preferences = "\n".join(f"- {p.preference}" for p in user.preferences)
    user_preferences = f"<user_preferences>\n{preferences}\n</user_preferences>"

    # 4. user notes
    notes = "\n".join(f"- {note.note}" for note in user.notes)
    user_notes = f"<user_notes>\n{notes}\n</user_notes>"

    # 5. put it all together
    system_prompt = (
        f"{request.system_prompt}\n\n"
        f"{user_profile}\n\n"
        f"{user_facts}\n\n"
        f"{user_preferences}\n\n"
        f"{user_notes}"
    )
    # print(f"\n--- System prompt ---\n{system_prompt}\n---------------------")
    return system_prompt
