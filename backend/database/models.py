from .connection import connect


def initialize_database() -> None:
    connection = connect()
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                specialty TEXT NOT NULL,
                qualification TEXT NOT NULL,
                experience_years INTEGER NOT NULL CHECK (experience_years >= 0),
                consultation_duration INTEGER NOT NULL DEFAULT 30 CHECK (consultation_duration > 0),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS doctor_slots (
                id INTEGER PRIMARY KEY,
                doctor_id INTEGER NOT NULL REFERENCES doctors(id),
                appointment_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                UNIQUE (doctor_id, appointment_date, start_time)
            );
            CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY,
                slot_id INTEGER NOT NULL REFERENCES doctor_slots(id),
                phone_number TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('BOOKED', 'CANCELLED')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                cancelled_at TEXT
            );
            CREATE UNIQUE INDEX IF NOT EXISTS uq_appointments_active_slot
                ON appointments(slot_id) WHERE status = 'BOOKED';
            CREATE INDEX IF NOT EXISTS ix_appointments_phone_status
                ON appointments(phone_number, status);
            CREATE INDEX IF NOT EXISTS ix_slots_date_active
                ON doctor_slots(appointment_date, is_active);
            """
        )
    finally:
        connection.close()
