from fastapi import APIRouter, HTTPException, Query

from services.appointments import get_appointments, mask_phone_number

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.get("")
def list_appointments(status: str | None = Query(default=None, pattern="^(BOOKED|CANCELLED)$"), date: str | None = None):
    try:
        rows = get_appointments(status, date)
        return [{**row, "phone_number": mask_phone_number(row["phone_number"])} for row in rows]
    except ValueError as exc:
        raise HTTPException(422, "Invalid date; use YYYY-MM-DD") from exc


@router.get("/{appointment_id}")
def appointment_details(appointment_id: str):
    row = next((item for item in get_appointments() if item["id"] == appointment_id), None)
    if row is None:
        raise HTTPException(404, "Appointment not found")
    return {**row, "phone_number": mask_phone_number(row["phone_number"])}
