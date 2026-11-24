from fastapi import APIRouter, HTTPException, Query

from database.schemas import DoctorResponse, DoctorSlotResponse
from services.appointments import get_doctor_by_id, get_doctor_slots, get_doctors

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


@router.get("", response_model=list[DoctorResponse])
def list_doctors(specialty: str | None = None):
    return get_doctors(specialty)


@router.get("/{doctor_id}", response_model=DoctorResponse)
def doctor_details(doctor_id: int):
    doctor = get_doctor_by_id(doctor_id)
    if doctor is None:
        raise HTTPException(404, "Doctor not found")
    return doctor


@router.get("/{doctor_id}/slots", response_model=list[DoctorSlotResponse])
def doctor_slots(doctor_id: int, date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")):
    if get_doctor_by_id(doctor_id) is None:
        raise HTTPException(404, "Doctor not found")
    try:
        return get_doctor_slots(doctor_id, date)
    except ValueError as exc:
        raise HTTPException(422, "Date must use YYYY-MM-DD") from exc
