from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from config import settings

from .connection import transaction

DOCTORS = (
    (1, "Dr. Sarah Mehta", "General Medicine", "MBBS, MD", 12),
    (2, "Dr. Arjun Rao", "Cardiology", "MBBS, DM", 15),
    (3, "Dr. Priya Shah", "Dermatology", "MBBS, MD", 8),
    (4, "Dr. Vikram Patel", "Orthopedics", "MBBS, MS", 10),
    (5, "Dr. Ananya Sharma", "Pediatrics", "MBBS, MD", 9),
)


def seed_database() -> None:
    zone = ZoneInfo(settings.app_timezone)
    today = datetime.now(zone).date()
    created_at = datetime.now(timezone.utc).isoformat()
    with transaction(immediate=True) as db:
        db.executemany(
            "INSERT OR IGNORE INTO doctors(id,name,specialty,qualification,experience_years,created_at) VALUES(?,?,?,?,?,?)",
            [(*doctor, created_at) for doctor in DOCTORS],
        )
        for offset in range(7):
            day = today + timedelta(days=offset)
            for doctor_id, *_ in DOCTORS:
                for start_hour, end_hour in ((9, 12), (14, 17)):
                    start = time(start_hour)
                    stop = time(end_hour)
                    while start < stop:
                        end_dt = datetime.combine(day, start) + timedelta(minutes=30)
                        db.execute(
                            "INSERT OR IGNORE INTO doctor_slots(doctor_id,appointment_date,start_time,end_time) VALUES(?,?,?,?)",
                            (doctor_id, day.isoformat(), start.strftime("%H:%M"), end_dt.strftime("%H:%M")),
                        )
                        start = end_dt.time()
