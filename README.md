# CareLine AI

CareLine AI is a React and FastAPI starter for a voice appointment assistant. The development stack runs in Docker Compose; Python and Node do not need to be installed on the host. The frontend uses Motion for React (formerly Framer Motion) for animations.

## Start the development stack

From the repository root, create local environment files from the examples:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Add provider credentials to `backend/.env` when they are available. Do not put provider keys in frontend variables. The initial health check works without provider credentials; voice features are not part of Ticket 1.

Build and start both services:

```powershell
docker compose up --build
```

Open [http://localhost:5173](http://localhost:5173). The backend health endpoint is [http://localhost:8000/api/health](http://localhost:8000/api/health).

## Development workflow

The `backend` and `frontend` source folders are bind-mounted into the containers. Backend dependencies are installed with `uv` from `backend/requirements.txt` into a container virtual environment. Python edits trigger Uvicorn reload; frontend edits use Vite HMR. Docker Desktop on Windows uses polling so host file changes are detected. Polling uses more CPU than native file events.

Python dependencies are installed in the backend image. Frontend dependencies live in a Docker-managed `node_modules` volume. After editing frontend dependencies in `package.json`, install them in the container with:

```powershell
docker compose run --rm frontend npm install --no-audit --no-fund
```

Rebuild after changing a Dockerfile or backend `requirements.txt`:

```powershell
docker compose up --build
```

Follow service logs:

```powershell
docker compose logs -f
```

Stop containers while keeping the SQLite data volume:

```powershell
docker compose down
```

The database file is stored in the `careline_data` named volume. `docker compose down -v` removes named volumes, including the database; use it only when you intend to erase local data.

## Appointment API

The backend initializes SQLite and seeds five fictional doctors with seven days of appointment slots on startup. The dashboard API is read-only:

- `GET /api/doctors?specialty=Cardiology`
- `GET /api/doctors/{doctor_id}`
- `GET /api/doctors/{doctor_id}/slots?date=YYYY-MM-DD`
- `GET /api/appointments?status=BOOKED&date=YYYY-MM-DD`
- `GET /api/appointments/{appointment_id}`
- `GET /api/dashboard/summary`

Appointment booking and cancellation are service functions only; public mutation endpoints are intentionally not exposed. Dashboard appointment responses mask phone numbers.

Run the focused backend tests from the repository root:

```powershell
docker compose exec backend python -m pytest tests -v
```
