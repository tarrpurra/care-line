from fastapi.testclient import TestClient

from config import settings
from main import app
from services.appointments import book_appointment, get_doctor_slots
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def test_read_apis_and_masked_phone(database, future_slot):
    booking = book_appointment(future_slot, "+14155552671", True)
    with TestClient(app) as client:
        assert len(client.get("/api/doctors").json()) == 5
        assert client.get("/api/doctors?specialty=Cardiology").json()[0]["name"] == "Dr. Arjun Rao"
        assert client.get("/api/health").status_code == 200
        response = client.get("/api/appointments?status=BOOKED")
        assert response.status_code == 200
        assert response.json()[0]["phone_number"] != "+14155552671"
        assert client.get("/api/dashboard/summary").json()["total_booked"] == 1
        assert client.get(f"/api/appointments/{booking['data']['appointment_id']}").status_code == 200
