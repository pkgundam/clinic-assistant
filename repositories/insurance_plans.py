from config.database import conn
from models.insurance_plan import InsurancePlan


def find_by_id(plan_id: int) -> InsurancePlan | None:
    """Return the insurance plan with this id, or None if there isn't one."""
    row = conn.execute(
        "select * from insurance_plans where id = %s and not void_sw",
        (plan_id,),
    ).fetchone()
    return InsurancePlan(**row) if row else None
