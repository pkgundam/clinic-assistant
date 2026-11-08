from models.clinic_user import ClinicUser


def alert_front_desk(clinic_user: ClinicUser, reason: str) -> None:
    """Tell the front desk about a patient. We have no alert system, so we only print it."""
    patient = clinic_user.profile
    print(f"[front desk] URGENT: {patient.full_name} (patient id {patient.id}) {reason}")
