from dotenv import load_dotenv

load_dotenv()

from dataclasses import asdict
from getpass import getpass
from uuid import uuid4

from agents.clinic_agent import ask
from services.auth import check_login, load_clinic_user


def login():
    """Ask for email and password until they match a user, then return that user."""
    while True:
        email = input("Email: ").strip()
        password = getpass("Password: ")

        user = check_login(email, password)
        if user:
            return user
        print("Invalid email or password\n")


def main():
    print("Clinic Appointment Booking Assistant")
    print("Please log in to continue")
    user = login()
    print(f"\nWelcome, {user.full_name}! You are logged in as a {user.role}.")

    # login is successful.
    # Show the whole user row, except the password hash.
    # print the user profile
    # row = asdict(user)
    # del row["password_hash"]
    # for column, value in row.items():
    #     print(f"  {column}: {value}")

    clinic_user = load_clinic_user(user)

    # One thread per chat session, so the agent remembers this conversation.
    thread_id = str(uuid4())

    print("\nClinic Assistant (type 'quit' to exit)")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue
        llm_answer = ask(user_input, clinic_user, thread_id)
        print(f"Assistant: {llm_answer}")


if __name__ == "__main__":
    main()
