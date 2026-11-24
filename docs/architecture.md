# Architecture

Ticket 1 uses two development containers joined by the default Docker Compose network:

- `frontend` serves the React app with Vite on port 5173. The browser calls the backend through the host-published port at `http://localhost:8000`.
- `backend` serves FastAPI on port 8000 and owns all provider credentials. Its health route is `GET /api/health`.
- Host source directories are bind-mounted for live code updates. Python and Node dependencies remain in container-managed environments/volumes.
- SQLite data is stored at `/app/data/careline.db` in the `careline_data` named volume.

The voice pipeline, appointment data model and business rules are intentionally deferred to later tickets.
