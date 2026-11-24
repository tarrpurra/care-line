from datetime import date, datetime, time, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import phonenumbers
from phonenumbers import NumberParseException
import sqlite3
import re

from config import settings
from database.connection import connect, transaction

ZONE = ZoneInfo(settings.app_timezone)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _tool(success: bool, code: str, message: str, data: dict | None = None) -> dict:
    return {"success": success, "code": code, "message": message, "data": data or {}}


def normalize_phone_number(value: str) -> str:
    raw = value.strip()
    try:
        number = phonenumbers.parse(raw, None if raw.startswith("+") else "IN")
    except NumberParseException as exc:
        raise ValueError("INVALID_PHONE_NUMBER") from exc
    if not phonenumbers.is_valid_number(number):
        raise ValueError("INVALID_PHONE_NUMBER")
    if not raw.startswith("+") and number.country_code != 91:
        raise ValueError("INVALID_PHONE_NUMBER")
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def _date(value: str | None) -> str:
    if value is not None and (not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)):
        raise ValueError("Invalid date")
    day = datetime.now(ZONE).date() if value is None else date.fromisoformat(value)
    return day.isoformat()


def _slot_is_past(day: str, start: str) -> bool:
    local = datetime.combine(date.fromisoformat(day), time.fromisoformat(start), ZONE)
    return local <= datetime.now(ZONE)


def _slot_row(db, slot_id: int):
    return db.execute(
        """SELECT s.*,d.name doctor_name,d.specialty,d.is_active doctor_active,
                  EXISTS(SELECT 1 FROM appointments a WHERE a.slot_id=s.id AND a.status='BOOKED') booked
           FROM doctor_slots s JOIN doctors d ON d.id=s.doctor_id WHERE s.id=?""",
        (slot_id,),
    ).fetchone()


def check_doctor_availability(doctor_id: int | None = None, doctor_name: str | None = None,
                              specialty: str | None = None, date: str | None = None) -> dict:
    try:
        requested_date = _date(date)
    except ValueError:
        return _tool(False, "INVALID_DATE", "Date must use YYYY-MM-DD.")
    db = connect()
    try:
        doctor_clauses, doctor_params = ["is_active=1"], []
        if doctor_id is not None:
            doctor_clauses.append("id=?"); doctor_params.append(doctor_id)
        if doctor_name:
            doctor_clauses.append("lower(name) LIKE ?"); doctor_params.append(f"%{doctor_name.strip().lower()}%")
        if specialty:
            doctor_clauses.append("lower(specialty)=?"); doctor_params.append(specialty.strip().lower())
        doctors = db.execute(
            f"SELECT id,name,specialty FROM doctors WHERE {' AND '.join(doctor_clauses)} ORDER BY name",
            doctor_params,
        ).fetchall()
        if not doctors and (doctor_id is not None or doctor_name):
            return _tool(False, "DOCTOR_NOT_FOUND", "No matching active doctor found.")
        if doctor_name and len(doctors) > 1:
            return _tool(False, "MULTIPLE_DOCTORS_FOUND", "Select a doctor to check availability.", {
                "doctors": [{"doctor_id": row["id"], "doctor_name": row["name"], "specialty": row["specialty"]} for row in doctors]
            })
        if not doctors:
            return _tool(False, "NO_AVAILABLE_SLOTS", "No matching doctors found.", {"doctors": []})
        doctor_ids = [doctor["id"] for doctor in doctors]
        placeholders = ",".join("?" for _ in doctor_ids)
        rows = db.execute(
            f"""SELECT d.id doctor_id,d.name doctor_name,d.specialty,s.id slot_id,
                       s.appointment_date,s.start_time,s.end_time
                FROM doctors d JOIN doctor_slots s ON s.doctor_id=d.id
                WHERE d.id IN ({placeholders}) AND d.is_active=1 AND s.is_active=1 AND s.appointment_date=?
                  AND NOT EXISTS(SELECT 1 FROM appointments a WHERE a.slot_id=s.id AND a.status='BOOKED')
                ORDER BY d.name,s.appointment_date,s.start_time""", (*doctor_ids, requested_date)
        ).fetchall()
        grouped = {}
        for row in rows:
            key = row["doctor_id"]
            doctor = grouped.setdefault(key, {"doctor_id": key, "doctor_name": row["doctor_name"],
                                               "specialty": row["specialty"], "date": requested_date,
                                               "available_slots": []})
            if not _slot_is_past(row["appointment_date"], row["start_time"]):
                doctor["available_slots"].append({"slot_id": row["slot_id"], "start_time": row["start_time"], "end_time": row["end_time"]})
        result = list(grouped.values())
        result = [doctor for doctor in result if doctor["available_slots"]]
        if not result:
            return _tool(False, "NO_AVAILABLE_SLOTS", "No available slots found.", {"doctors": []})
        return _tool(True, "AVAILABILITY_FOUND", "Available slots found.", {"doctors": result})
    finally:
        db.close()


def book_appointment(slot_id: int, phone_number: str, phone_confirmed: bool = False) -> dict:
    if not phone_confirmed:
        return _tool(False, "PHONE_NOT_CONFIRMED", "Caller phone number must be confirmed.")
    try:
        phone = normalize_phone_number(phone_number)
    except ValueError:
        return _tool(False, "INVALID_PHONE_NUMBER", "Phone number is invalid.")
    now = _now().isoformat()
    try:
        with transaction(immediate=True) as db:
            slot = _slot_row(db, slot_id)
            if slot is None:
                return _tool(False, "SLOT_NOT_FOUND", "Slot not found.")
            if not slot["is_active"] or not slot["doctor_active"]:
                return _tool(False, "SLOT_UNAVAILABLE", "Slot is inactive.")
            if _slot_is_past(slot["appointment_date"], slot["start_time"]):
                return _tool(False, "PAST_SLOT", "Appointment time has passed.")
            if slot["booked"]:
                return _tool(False, "SLOT_UNAVAILABLE", "Slot is already booked.")
            appointment_id = str(uuid4())
            db.execute("INSERT INTO appointments(id,slot_id,phone_number,status,created_at,updated_at) VALUES(?,?,?,'BOOKED',?,?)",
                       (appointment_id, slot_id, phone, now, now))
        return _tool(True, "APPOINTMENT_BOOKED", "Your appointment has been booked successfully.",
                     {"appointment_id": appointment_id, "doctor_name": slot["doctor_name"], "specialty": slot["specialty"],
                      "date": slot["appointment_date"], "start_time": slot["start_time"], "end_time": slot["end_time"], "status": "BOOKED"})
    except sqlite3.IntegrityError:
        return _tool(False, "SLOT_UNAVAILABLE", "Slot is already booked or unavailable.")
    except sqlite3.Error:
        return _tool(False, "DATABASE_ERROR", "Appointment could not be saved.")


def cancel_appointment(phone_number: str, appointment_id: str | None = None, phone_confirmed: bool = False) -> dict:
    if not phone_confirmed:
        return _tool(False, "PHONE_NOT_CONFIRMED", "Caller phone number must be confirmed.")
    try:
        phone = normalize_phone_number(phone_number)
    except ValueError:
        return _tool(False, "INVALID_PHONE_NUMBER", "Phone number is invalid.")
    now = _now()
    try:
        with transaction(immediate=True) as db:
            rows = db.execute(
                """SELECT a.id appointment_id,a.status,s.id slot_id,s.appointment_date,s.start_time,s.end_time,
                          d.name doctor_name,d.specialty
                   FROM appointments a JOIN doctor_slots s ON s.id=a.slot_id JOIN doctors d ON d.id=s.doctor_id
                   WHERE a.phone_number=? AND a.status='BOOKED' ORDER BY s.appointment_date,s.start_time""", (phone,)
            ).fetchall()
            eligible = [r for r in rows if not _slot_is_past(r["appointment_date"], r["start_time"])]
            if appointment_id:
                selected = next((r for r in rows if r["appointment_id"] == appointment_id), None)
                if selected is None:
                    exists = db.execute("SELECT status FROM appointments WHERE id=? AND phone_number=?", (appointment_id, phone)).fetchone()
                    code = "APPOINTMENT_ALREADY_CANCELLED" if exists and exists["status"] == "CANCELLED" else "APPOINTMENT_NOT_FOUND"
                    return _tool(False, code, "No eligible appointment found.")
                if selected not in eligible:
                    return _tool(False, "PAST_SLOT", "Past appointments cannot be cancelled through this service.")
            elif len(eligible) > 1:
                return _tool(False, "MULTIPLE_APPOINTMENTS_FOUND", "Select an appointment to cancel.",
                             {"appointments": [{"appointment_id":r["appointment_id"],"doctor_name":r["doctor_name"],"date":r["appointment_date"],"start_time":r["start_time"]} for r in eligible]})
            elif not eligible:
                return _tool(False, "APPOINTMENT_NOT_FOUND", "No upcoming booking found.")
            else:
                selected = eligible[0]
            updated = db.execute("UPDATE appointments SET status='CANCELLED',updated_at=?,cancelled_at=? WHERE id=? AND status='BOOKED'",
                                 (now.isoformat(), now.isoformat(), selected["appointment_id"]))
            if updated.rowcount != 1:
                return _tool(False, "APPOINTMENT_NOT_FOUND", "No eligible appointment found.")
            return _tool(True, "APPOINTMENT_CANCELLED", "Your appointment has been cancelled successfully.",
                         {"appointment_id":selected["appointment_id"],"doctor_name":selected["doctor_name"],"date":selected["appointment_date"],"start_time":selected["start_time"],"status":"CANCELLED"})
    except sqlite3.Error:
        return _tool(False, "DATABASE_ERROR", "Appointment could not be cancelled.")


def _rows(query: str, params=()):
    db = connect()
    try:
        return [dict(row) for row in db.execute(query, params).fetchall()]
    finally:
        db.close()


def get_doctors(specialty: str | None = None):
    query = "SELECT id,name,specialty,qualification,experience_years,consultation_duration FROM doctors WHERE is_active=1"
    params = ()
    if specialty:
        query += " AND lower(specialty)=lower(?)"; params = (specialty.strip(),)
    return _rows(query + " ORDER BY name", params)


def get_doctor_by_id(doctor_id: int):
    rows = _rows("SELECT id,name,specialty,qualification,experience_years,consultation_duration FROM doctors WHERE id=? AND is_active=1", (doctor_id,))
    return rows[0] if rows else None


def get_doctor_slots(doctor_id: int, date: str | None = None):
    requested = _date(date)
    rows = _rows("""SELECT s.id slot_id,s.doctor_id,s.appointment_date,s.start_time,s.end_time,
                  NOT EXISTS(SELECT 1 FROM appointments a WHERE a.slot_id=s.id AND a.status='BOOKED') is_available
                  FROM doctor_slots s JOIN doctors d ON d.id=s.doctor_id
                  WHERE s.doctor_id=? AND d.is_active=1 AND s.is_active=1 AND s.appointment_date=?
                  ORDER BY s.start_time""", (doctor_id, requested))
    return [r for r in rows if not _slot_is_past(r["appointment_date"], r["start_time"])]


def get_appointments(status: str | None = None, date: str | None = None):
    clauses, params = ["1=1"], []
    if status:
        clauses.append("a.status=?"); params.append(status.upper())
    if date:
        clauses.append("s.appointment_date=?"); params.append(_date(date))
    return _rows(f"""SELECT a.id,a.slot_id,s.doctor_id,d.name doctor_name,d.specialty,s.appointment_date,
                  s.start_time,s.end_time,a.phone_number,a.status,a.created_at
                  FROM appointments a JOIN doctor_slots s ON s.id=a.slot_id JOIN doctors d ON d.id=s.doctor_id
                  WHERE {' AND '.join(clauses)} ORDER BY s.appointment_date,s.start_time""", params)


def get_appointments_by_phone(phone_number: str):
    phone = normalize_phone_number(phone_number)
    return _rows("SELECT id,slot_id,phone_number,status,created_at,updated_at,cancelled_at FROM appointments WHERE phone_number=? ORDER BY created_at DESC", (phone,))


def get_dashboard_summary():
    today = datetime.now(ZONE).date().isoformat()
    db = connect()
    try:
        available_today = db.execute("""SELECT s.appointment_date,s.start_time FROM doctor_slots s JOIN doctors d ON d.id=s.doctor_id
            WHERE s.appointment_date=? AND s.is_active=1 AND d.is_active=1
            AND NOT EXISTS(SELECT 1 FROM appointments a WHERE a.slot_id=s.id AND a.status='BOOKED')""", (today,)).fetchall()
        return {
            "total_doctors": db.execute("SELECT count(*) FROM doctors WHERE is_active=1").fetchone()[0],
            "available_slots_today": sum(not _slot_is_past(r["appointment_date"], r["start_time"]) for r in available_today),
            "appointments_today": db.execute("""SELECT count(*) FROM appointments a JOIN doctor_slots s ON s.id=a.slot_id
                WHERE s.appointment_date=? AND a.status='BOOKED'""", (today,)).fetchone()[0],
            "total_booked": db.execute("SELECT count(*) FROM appointments WHERE status='BOOKED'").fetchone()[0],
            "total_cancelled": db.execute("SELECT count(*) FROM appointments WHERE status='CANCELLED'").fetchone()[0],
        }
    finally:
        db.close()


def mask_phone_number(phone: str) -> str:
    return phone[:3] + "****" + phone[-3:] if len(phone) > 7 else "****"
