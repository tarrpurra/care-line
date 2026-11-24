from pydantic import BaseModel


class DoctorResponse(BaseModel):
    id: int
    name: str
    specialty: str
    qualification: str
    experience_years: int
    consultation_duration: int


class DoctorSlotResponse(BaseModel):
    slot_id: int
    doctor_id: int
    appointment_date: str
    start_time: str
    end_time: str
    is_available: bool


class AppointmentResponse(BaseModel):
    id: str
    slot_id: int
    doctor_id: int
    doctor_name: str
    specialty: str
    appointment_date: str
    start_time: str
    end_time: str
    phone_number: str
    status: str
    created_at: str


class DashboardSummary(BaseModel):
    total_doctors: int
    available_slots_today: int
    appointments_today: int
    total_booked: int
    total_cancelled: int


class ToolResponse(BaseModel):
    success: bool
    code: str
    message: str
    data: dict
