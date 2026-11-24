# TICKET-02: Database Schema, Mock Data & Appointment Management Tools

**Project:** CareLine AI  
**Priority:** P0 – Critical  
**Status:** Completed (13 backend tests passed; live API verification passed)
**Estimated effort:** 60–90 minutes  
**Dependency:** TICKET-01 – Completed  
**Repository:** https://github.com/tarrpurra/care-line

## 1. Objective

Implement the complete appointment management backend using SQLite, realistic mock doctor data, reusable business logic and REST APIs.

The backend must support checking doctor availability, booking appointments and cancelling appointments. These functions will later be registered as callable tools in the Pipecat voice pipeline.

The database must act as the single source of truth for both the voice agent and frontend dashboard.

## 2. Existing Architecture

Continue using the existing repository structure and configuration:

- FastAPI backend.
- React + TypeScript frontend.
- Docker Compose development environment.
- Persistent SQLite Docker volume.
- Existing `config.py` and `settings` object.
- Configurable `DATABASE_PATH`.
- Configurable `APP_TIMEZONE`, currently `Asia/Kolkata`.

Do not recreate the repository or replace the existing Docker configuration unnecessarily.

Use Python's built-in `sqlite3` module. An additional ORM is not required.

## 3. Database Design

Implement three relational tables.

### 3.1 Doctors Table

Table name: `doctors`

| Column | Type | Constraint |
|---|---|---|
| id | INTEGER | Primary key |
| name | TEXT | Not null |
| specialty | TEXT | Not null |
| qualification | TEXT | Not null |
| experience_years | INTEGER | Non-negative |
| consultation_duration | INTEGER | Default 30 minutes |
| is_active | BOOLEAN | Default true |
| created_at | TEXT | Not null |

### 3.2 Doctor Slots Table

Table name: `doctor_slots`

| Column | Type | Constraint |
|---|---|---|
| id | INTEGER | Primary key |
| doctor_id | INTEGER | Foreign key |
| appointment_date | TEXT | YYYY-MM-DD |
| start_time | TEXT | HH:MM |
| end_time | TEXT | HH:MM |
| is_active | BOOLEAN | Default true |

Add a unique constraint on:

`doctor_id + appointment_date + start_time`

Slot availability must be derived from whether an active booking exists for the slot.

Do not maintain a separate mutable `is_booked` flag, as this could create inconsistent booking states.

### 3.3 Appointments Table

Table name: `appointments`

| Column | Type | Constraint |
|---|---|---|
| id | TEXT | Primary key, UUID |
| slot_id | INTEGER | Foreign key |
| phone_number | TEXT | Not null |
| status | TEXT | BOOKED or CANCELLED |
| created_at | TEXT | Not null |
| updated_at | TEXT | Not null |
| cancelled_at | TEXT | Nullable |

Create a partial unique index on `slot_id` where `status = 'BOOKED'` to prevent multiple active appointments for the same slot.

Add an index on `phone_number` and `status` for efficient appointment lookup.

Store timestamps consistently in UTC and interpret appointment dates and times using `APP_TIMEZONE`.

Do not require patient names, email addresses, passwords or OTP verification.

## 4. Database Initialization

Implement `backend/database/connection.py`.

- [x] Read the database path from the existing settings.
- [x] Automatically create the database directory if missing.
- [x] Establish SQLite connections.
- [x] Enable foreign key enforcement on every connection.
- [x] Enable WAL mode.
- [x] Configure a reasonable busy timeout.
- [x] Use parameterized SQL queries.
- [x] Implement safe transaction handling.
- [x] Ensure connections are properly closed.

Implement `backend/database/models.py`.

- [x] Create the doctors table.
- [x] Create the doctor_slots table.
- [x] Create the appointments table.
- [x] Create all required indexes and constraints.
- [x] Implement idempotent schema initialization.

Update the existing FastAPI lifespan function in `main.py` to initialize the database and seed mock data automatically on startup.

## 5. Mock Data Generation

Implement `backend/database/seed.py`.

Create the following fictional doctors:

| ID | Doctor | Specialty | Qualification | Experience |
|---|---|---|---|---|
| 1 | Dr. Sarah Mehta | General Medicine | MBBS, MD | 12 years |
| 2 | Dr. Arjun Rao | Cardiology | MBBS, DM | 15 years |
| 3 | Dr. Priya Shah | Dermatology | MBBS, MD | 8 years |
| 4 | Dr. Vikram Patel | Orthopedics | MBBS, MS | 10 years |
| 5 | Dr. Ananya Sharma | Pediatrics | MBBS, MD | 9 years |

Generate appointment slots dynamically for the next seven calendar days, including today.

Default appointment schedule:

- 09:00 AM – 12:00 PM
- 02:00 PM – 05:00 PM
- 30-minute appointment duration.
- 12 slots per doctor per day.
- 5 doctors.
- Up to 420 generated slots across seven days.

Seed data requirements:

- [x] Generate dates relative to the configured application timezone.
- [x] Use stable doctor IDs.
- [x] Prevent duplicate doctors.
- [x] Prevent duplicate slots.
- [x] Preserve existing appointments when the server restarts.
- [x] Generate missing future slots on subsequent startups.
- [x] Exclude past slots from availability results.
- [x] Use synthetic phone numbers for any test fixtures.
- [x] Do not automatically populate bookings unless explicitly requested in a demo seed command.

## 6. Appointment Management Service

Implement the business logic in:

`backend/services/appointments.py`

All business logic must remain independent of Pipecat, Gemini and the frontend.

### 6.1 Tool: check_doctor_availability

Purpose: Return available appointment slots for a selected doctor, specialty or date.

Function signature:

```python
check_doctor_availability(
    doctor_id: int | None = None,
    doctor_name: str | None = None,
    specialty: str | None = None,
    date: str | None = None
) -> dict
```

Requirements:

- [x] Support doctor ID lookup, including a `DOCTOR_NOT_FOUND` response for unknown/inactive IDs.
- [x] Support case-insensitive doctor name matching.
- [x] Support specialty-based filtering.
- [x] Support date-based filtering.
- [x] Default to the current date when no date is provided.
- [x] Exclude inactive doctors.
- [x] Exclude inactive slots.
- [x] Exclude already booked slots.
- [x] Exclude past slots.
- [x] Return results sorted by date and time.
- [x] Return a structured response when no slots are available.
- [x] Return `MULTIPLE_DOCTORS_FOUND` with candidates when a name matches multiple doctors.

Example response:

```json
{
  "success": true,
  "code": "AVAILABILITY_FOUND",
  "message": "Available slots found.",
  "data": {
    "doctor_id": 1,
    "doctor_name": "Dr. Sarah Mehta",
    "specialty": "General Medicine",
    "date": "2026-11-25",
    "available_slots": [
      {
        "slot_id": 101,
        "start_time": "09:00",
        "end_time": "09:30"
      },
      {
        "slot_id": 102,
        "start_time": "09:30",
        "end_time": "10:00"
      }
    ]
  }
}
```

The response structure must also support multiple matching doctors.

### 6.2 Tool: book_appointment

Purpose: Book a selected available slot using the caller's confirmed phone number.

Function signature:

```python
book_appointment(
    slot_id: int,
    phone_number: str,
    phone_confirmed: bool = False
) -> dict
```

Requirements:

- [x] Validate and normalize the phone number.
- [x] Reject unconfirmed phone numbers.
- [x] Verify the slot exists.
- [x] Verify the doctor and slot are active.
- [x] Verify the appointment is not in the past.
- [x] Verify the slot is still available.
- [x] Generate a unique appointment UUID.
- [x] Create the appointment with status `BOOKED`.
- [x] Execute validation and booking inside a single transaction.
- [x] Handle database uniqueness conflicts gracefully.
- [x] Prevent simultaneous requests from double-booking a slot.
- [x] Return the confirmed appointment details.

Example response:

```json
{
  "success": true,
  "code": "APPOINTMENT_BOOKED",
  "message": "Your appointment has been booked successfully.",
  "data": {
    "appointment_id": "generated-uuid",
    "doctor_name": "Dr. Sarah Mehta",
    "specialty": "General Medicine",
    "date": "2026-11-25",
    "start_time": "09:00",
    "end_time": "09:30",
    "status": "BOOKED"
  }
}
```

The `phone_confirmed` argument is an internal service parameter. In Ticket 04, it must be supplied by server-side conversation state after the caller confirms their spoken number, not by trusting an arbitrary LLM-generated boolean.

### 6.3 Tool: cancel_appointment

Purpose: Cancel an existing appointment associated with the caller's confirmed phone number.

Function signature:

```python
cancel_appointment(
    phone_number: str,
    appointment_id: str | None = None,
    phone_confirmed: bool = False
) -> dict
```

Requirements:

- [x] Validate and normalize the phone number.
- [x] Reject unconfirmed phone numbers.
- [x] Find upcoming active appointments associated with the phone number.
- [x] Cancel the appointment if exactly one eligible booking exists.
- [x] Return eligible appointment options if multiple bookings exist.
- [x] Require appointment selection when multiple appointments exist.
- [x] Verify that the selected appointment belongs to the confirmed phone number.
- [x] Update status to `CANCELLED`.
- [x] Record the cancellation timestamp.
- [x] Preserve the appointment record for history.
- [x] Make the released slot available again automatically.
- [x] Handle already cancelled or nonexistent appointments gracefully.

Example response:

```json
{
  "success": true,
  "code": "APPOINTMENT_CANCELLED",
  "message": "Your appointment has been cancelled successfully.",
  "data": {
    "appointment_id": "generated-uuid",
    "doctor_name": "Dr. Sarah Mehta",
    "date": "2026-11-25",
    "start_time": "09:00",
    "status": "CANCELLED"
  }
}
```

### 6.4 Supporting Functions

Implement the following reusable functions:

```python
get_doctors()

get_doctor_by_id(doctor_id)

get_doctor_slots(doctor_id, date=None)

get_appointments(status=None, date=None)

get_appointments_by_phone(phone_number)

get_dashboard_summary()

normalize_phone_number(phone_number)
```

Use a consistent structured response format for the three agent-facing appointment tools.

## 7. Business Rules and Error Handling

Implement machine-readable response codes so the LLM can understand results reliably.

| Error code | Description |
|---|---|
| DOCTOR_NOT_FOUND | Doctor does not exist |
| MULTIPLE_DOCTORS_FOUND | Doctor selection required |
| NO_AVAILABLE_SLOTS | No suitable available appointments |
| INVALID_PHONE_NUMBER | Phone number format is invalid |
| PHONE_NOT_CONFIRMED | Caller confirmation is required |
| INVALID_DATE | Date format is invalid |
| SLOT_NOT_FOUND | Requested slot does not exist |
| SLOT_UNAVAILABLE | Slot is already booked or inactive |
| PAST_SLOT | Appointment time has passed |
| APPOINTMENT_NOT_FOUND | No matching appointment exists |
| MULTIPLE_APPOINTMENTS_FOUND | Caller must select an appointment |
| APPOINTMENT_ALREADY_CANCELLED | Appointment is already cancelled |
| DATABASE_ERROR | Unexpected database operation failure |

Additional rules:

- Use strings to store phone numbers.
- Normalize Indian phone numbers into a consistent format, such as E.164 with the `+91` country code.
- Accept valid international numbers when an explicit country code is provided.
- Do not silently correct missing or incorrect digits.
- Never identify a caller using their name.
- Do not allow cancellation of another phone number's appointment.
- Do not permanently delete cancelled appointments.
- Do not expose raw SQL errors to users.
- Avoid logging full phone numbers.
- Do not expose real patient information.

## 8. REST API Development

Implement the following read-only endpoints for the frontend dashboard.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/doctors | List active doctors |
| GET | /api/doctors/{doctor_id} | Doctor details |
| GET | /api/doctors/{doctor_id}/slots | Doctor availability |
| GET | /api/appointments | List appointments |
| GET | /api/appointments/{appointment_id} | Appointment details |
| GET | /api/dashboard/summary | Dashboard statistics |

Supported query parameters:

```text
GET /api/doctors?specialty=Cardiology

GET /api/doctors/1/slots?date=2026-11-25

GET /api/appointments?status=BOOKED

GET /api/appointments?date=2026-11-25
```

Dashboard summary example:

```json
{
  "total_doctors": 5,
  "available_slots_today": 40,
  "appointments_today": 8,
  "total_booked": 12,
  "total_cancelled": 2
}
```

All dashboard statistics must be calculated from the database rather than hardcoded.

Use masked phone numbers in public dashboard responses.

Do not expose public booking or cancellation mutation endpoints in this ticket. Test mutations directly through the service layer. The Pipecat agent will execute these operations in a later ticket.

## 9. Pydantic Schemas

Create `backend/database/schemas.py` or an equivalent dedicated schema module.

Implement typed response and validation models:

- DoctorResponse
- DoctorSlotResponse
- AppointmentResponse
- AvailabilityResponse
- DashboardSummary
- ToolResponse

Ensure API responses are consistent and JSON serializable.

## 10. Expected File Changes

```text
backend/
├── main.py                     # Update lifespan and routers
├── config.py                   # Reuse existing settings
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── models.py
│   ├── schemas.py
│   └── seed.py
├── services/
│   ├── __init__.py
│   └── appointments.py
├── routes/
│   ├── __init__.py
│   ├── doctors.py
│   ├── appointments.py
│   └── dashboard.py
└── tests/
    ├── conftest.py
    ├── test_database.py
    ├── test_appointments.py
    └── test_api.py
```

Update dependencies only when necessary for testing or phone validation.

Preserve the existing frontend, Docker Compose and environment configuration.

## 11. Testing Requirements

Use Pytest with an isolated temporary SQLite database.

| Test ID | Scenario | Expected result |
|---|---|---|
| TC-01 | Initialize database | All tables created |
| TC-02 | Seed database twice | No duplicate doctors or slots |
| TC-03 | Fetch doctors | Five active mock doctors |
| TC-04 | Filter by specialty | Correct doctors returned |
| TC-05 | Check availability | Available future slots returned |
| TC-06 | Book valid slot | Appointment created |
| TC-07 | Book the same slot twice | Second booking rejected |
| TC-08 | Concurrent booking requests | Only one booking succeeds |
| TC-09 | Invalid phone number | Booking rejected |
| TC-10 | Unconfirmed phone number | Booking rejected |
| TC-11 | Book a past slot | Booking rejected |
| TC-12 | Cancel an appointment | Status updated |
| TC-13 | Check cancelled slot | Slot becomes available |
| TC-14 | Cancel nonexistent appointment | Structured error returned |
| TC-15 | Multiple active appointments | Selection required |
| TC-16 | Cancel using wrong phone number | Cancellation rejected |
| TC-17 | Restart database initialization | Bookings preserved |
| TC-18 | Verify dashboard statistics | Accurate calculated values |
| TC-19 | Test REST endpoints | Correct HTTP and JSON responses |
| TC-20 | Inspect dashboard responses | Phone numbers masked |

Tests must not require Gemini or ElevenLabs API credentials.

## 12. Execution and Verification

Start the existing Docker Compose environment:

```bash
docker compose up --build
```

Verify the backend:

```text
http://localhost:8000/api/health

http://localhost:8000/api/doctors

http://localhost:8000/api/doctors/1/slots

http://localhost:8000/api/appointments

http://localhost:8000/api/dashboard/summary

http://localhost:8000/docs
```

Use Swagger UI to verify the dashboard API responses.

Run the automated test suite inside the backend container:

```bash
docker compose exec backend python -m pytest tests -v
```

Ensure test dependencies are available in the development container.

## 13. Acceptance Criteria

- [x] SQLite database initializes automatically on backend startup.
- [x] Database persists using the existing Docker volume (Compose uses the `careline_data` named volume; persistence across recreation was reported by the user).
- [x] Five fictional doctors are populated.
- [x] Rolling seven-day appointment slots are generated.
- [x] Availability function behavior and doctor-selection responses are implemented; related tests passed.
- [x] Booking function works correctly; booking and concurrency tests passed.
- [x] Cancellation function works correctly (including multiple appointments, repeat cancellation, ownership checks, and structured database errors).
- [x] Phone number validation is implemented.
- [x] Unconfirmed phone numbers are rejected.
- [x] Duplicate bookings are prevented at the database level.
- [x] Concurrent bookings are handled safely (serialized transaction; concurrent booking test passed).
- [x] Cancelled slots become available again (derived from active bookings; slot-release test passed).
- [x] REST APIs are accessible through Swagger UI (`/docs`, `/openapi.json`, and required API routes returned HTTP 200).
- [x] Dashboard statistics are calculated from database records.
- [x] Existing health endpoint remains functional (live endpoint returned HTTP 200 with `status: healthy`).
- [x] Automated tests pass (13 passed in the backend container).
- [x] README is updated with database and testing instructions.

## 14. Out of Scope

Do not implement the following in this ticket:

- Pipecat voice pipeline.
- Gemini function registration.
- ElevenLabs integration.
- WebRTC connections.
- Live transcript.
- Conversation-based phone confirmation.
- Frontend dashboard redesign.
- Real-time dashboard events.
- LangChain or LangGraph.
- Authentication or OTP.

These features will be implemented in subsequent tickets.

## 15. Definition of Done

The backend can independently check doctor availability, book appointments and cancel appointments with reliable database persistence, validation, concurrency protection and structured responses.

All required dashboard APIs are working, and the service functions are ready to be registered as Pipecat tools.

## 16. Implementation Report

After completing this ticket, provide:

1. Summary of implemented features.
2. List of created and modified files.
3. Database schema summary.
4. Available API endpoints.
5. Automated test results.
6. Any unresolved issues.
7. Steps to verify the implementation manually.

Suggested Git commit:

```bash
git commit -m "feat: implement database and appointment management services"
```

