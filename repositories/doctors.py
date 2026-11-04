from config.database import conn
from models.doctor import Doctor


def get_all() -> list[Doctor]:
    """Return every active doctor."""
    rows = conn.execute("select * from doctors where not void_sw order by id").fetchall()
    return [Doctor(**row) for row in rows]


def find_by_id(doctor_id: int) -> Doctor | None:
    """Return the doctor with this id, or None if there isn't one."""
    row = conn.execute(
        "select * from doctors where id = %s and not void_sw",
        (doctor_id,),
    ).fetchone()
    return Doctor(**row) if row else None
