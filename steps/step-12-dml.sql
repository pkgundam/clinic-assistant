-- David (admin), Sachin and Brian log in with the demo password: clinicdemo
-- (only the bcrypt hash is stored). db/setup.py does this too when it reseeds.
update users
set password_hash = '$2b$12$UKCdQWdpiF4RpfTqs05JW.p9lSiXpqhghQrdnWJStpJSsXl1zwDv6',
    updated_at = now(),
    updated_by = id
where email in ('david@example.com', 'sachin@example.com', 'brian@example.com');
