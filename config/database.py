import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

# Connect once when this module is first imported. Every other file does
# `from config.database import conn` and reuses this same connection.
conn = psycopg.connect(
    os.environ["DATABASE_URL"],
    autocommit=True,
    row_factory=dict_row,
)
