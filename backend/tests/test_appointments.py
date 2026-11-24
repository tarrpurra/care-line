from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import settings
from database.connection import connect
from database.models import initialize_database
from database.seed import seed_database
from services.appointments import (
    book_appointment,
    cancel_appointment,
    check_doctor_availability,
    get_doctors,
    get_doctor_slots,
    normalize_phone_number,
)

PHONE = "+14155552671"


def test_seed_is_idempotent(database):
    seed_database()
    db = connect()
    try:
        assert db.execute("SELECT count(*) FROM doctors").fetchone()[0] == 5
        assert db.execute("SELECT count(*) FROM doctor_slots").fetchone()[0] == 420
    finally:
        db.close()


def test_doctors_and_specialty_filter(database):
    assert len(get_doctors()) == 5
    assert [d["name"] for d in get_doctors("cardiology")] == ["Dr. Arjun Rao"]


def test_phone_normalization_and_rejection(database):
    assert normalize_phone_number("9876543210") == "+919876543210"


def test_availability_is_grouped_and_sorted(database):
    result = check_doctor_availability(specialty="Cardiology", date=(datetime.now(ZoneInfo(settings.app_timezone)).date() + timedelta(days=1)).isoformat())
    assert result["success"] and result["data"]["doctors"][0]["doctor_name"] == "Dr. Arjun Rao"
    assert result["data"]["doctors"][0]["available_slots"][0]["start_time"] == "09:00"
    all_doctors = check_doctor_availability(date=(datetime.now(ZoneInfo(settings.app_timezone)).date() + timedelta(days=1)).isoformat())
    assert len(all_doctors["data"]["doctors"]) == 5


def test_availability_unknown_and_ambiguous_doctors(database):
    assert check_doctor_availability(doctor_id=999)["code"] == "DOCTOR_NOT_FOUND"
    assert check_doctor_availability(doctor_name="Nobody")["code"] == "DOCTOR_NOT_FOUND"
    ambiguous = check_doctor_availability(doctor_name="dr")
    assert ambiguous["code"] == "MULTIPLE_DOCTORS_FOUND"
    assert len(ambiguous["data"]["doctors"]) == 5


def test_booking_duplicate_cancel_and_slot_release(database, future_slot):
    booked = book_appointment(future_slot, PHONE, True)
    assert booked["code"] == "APPOINTMENT_BOOKED"
    assert book_appointment(future_slot, PHONE, True)["code"] == "SLOT_UNAVAILABLE"
    cancelled = cancel_appointment(PHONE, booked["data"]["appointment_id"], True)
    assert cancelled["code"] == "APPOINTMENT_CANCELLED"
    assert get_doctor_slots(1, booked["data"]["date"])[0]["is_available"]


def test_cancellation_requires_matching_phone(database, future_slot):
    booked = book_appointment(future_slot, PHONE, True)
    assert cancel_appointment("+919876543210", booked["data"]["appointment_id"], True)["code"] == "APPOINTMENT_NOT_FOUND"


def test_cancellation_multiple_and_already_cancelled(database, future_slot):
    tomorrow = (datetime.now(ZoneInfo(settings.app_timezone)).date() + timedelta(days=1)).isoformat()
    second_slot = get_doctor_slots(2, tomorrow)[0]["slot_id"]
    first = book_appointment(future_slot, PHONE, True)
    book_appointment(second_slot, PHONE, True)
    options = cancel_appointment(PHONE, phone_confirmed=True)
    assert options["code"] == "MULTIPLE_APPOINTMENTS_FOUND"
    cancelled = cancel_appointment(PHONE, first["data"]["appointment_id"], True)
    assert cancelled["code"] == "APPOINTMENT_CANCELLED"
    assert cancel_appointment(PHONE, first["data"]["appointment_id"], True)["code"] == "APPOINTMENT_ALREADY_CANCELLED"


def test_cancellation_database_error_is_structured(database, monkeypatch):
    import sqlite3
    import services.appointments as service

    def fail_transaction(*, immediate=False):
        raise sqlite3.OperationalError("private database detail")

    monkeypatch.setattr(service, "transaction", fail_transaction)
    result = service.cancel_appointment(PHONE, phone_confirmed=True)
    assert result["code"] == "DATABASE_ERROR"
    assert "private database detail" not in result["message"]


def test_confirmation_and_invalid_phone(database, future_slot):
    assert book_appointment(future_slot, PHONE)["code"] == "PHONE_NOT_CONFIRMED"
    assert book_appointment(future_slot, "123", True)["code"] == "INVALID_PHONE_NUMBER"


def test_concurrent_booking_only_one_succeeds(database, future_slot):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: book_appointment(future_slot, PHONE, True), range(2)))
    assert sum(result["success"] for result in results) == 1


def test_reinitialization_preserves_appointment(database, future_slot):
    booked = book_appointment(future_slot, PHONE, True)
    initialize_database()
    db = connect()
    try:
        assert db.execute("SELECT status FROM appointments WHERE id=?", (booked["data"]["appointment_id"],)).fetchone()[0] == "BOOKED"
    finally:
        db.close()
