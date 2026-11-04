Step-2
In this step, lets add a simple login for the assistant to know who is logged in.
add a very simple login (no signup yet).

0. install bcrypt using uv.
1. create a folder called config
   inside it create database.py, connect to the DB once and export the connection. reuse it everywhere.
2. create a folder called models
   inside it create user.py with a User dataclass (id, full_name, email, password_hash, role, etc.. the user profile columns)
3. create a folder called repositories
   inside it create users.py with a method find_by_email(email) that returns a User or None
4. update chat.py to log in before the chat starts
   ask for email and password
   check the password with bcrypt.checkpw
   wrong -> "Invalid email or password", ask again
   right -> greet the user by name and their role and start the chat.
   Also print the entire user row minus the password hash.
5. test with priya@example.com / clinicdemo
