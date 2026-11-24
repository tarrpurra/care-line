# TICKET-01: Project Initialization & Environment Setup

**Priority:** P0 – Critical  
**Status:** In Progress — runtime checks reported complete; Git setup remains to verify  
**Estimated effort:** 30–45 minutes  
**Dependencies:** None

## 1. Objective

Initialize the Voice AI Doctor Appointment Assistant project with a clean, modular full-stack architecture. Configure the development environments, required dependencies and API credentials to establish the foundation for subsequent implementation.

## 2. Technology Stack

| Component | Technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| UI | Tailwind CSS + shadcn/ui |
| Backend | Python + FastAPI |
| Voice Framework | Pipecat |
| Speech-to-Text | ElevenLabs |
| Text-to-Speech | ElevenLabs |
| LLM | Google Gemini Flash |
| Audio Transport | SmallWebRTC |
| Voice Activity Detection | Silero VAD |
| Database | SQLite |
| Version Control | Git + GitHub |

**Architecture constraint:** Use Pipecat's native LLM integration and function calling. Do not introduce LangChain, LangGraph, Redis or unnecessary orchestration frameworks.

**Development runtime:** Run the frontend and backend in Docker Compose. Install their runtime dependencies in their respective images, and mount the source directories from the host so code edits are visible inside the running containers. Enable Vite HMR and FastAPI/Uvicorn reload so application code changes appear without manually restarting containers. Keep dependency directories inside containers or named volumes so host bind mounts do not hide installed dependencies. Persist SQLite data in a named Docker volume. Dependency or image configuration changes may require rebuilding the affected image; source code changes must not.

## 3. Implementation Tasks

### 3.1 Repository Initialization

- [ ] Initialize the Git repository with the name `careline-ai`.
- [x] Create separate frontend and backend directories.
- [x] Add `docker-compose.yml` to run the frontend and backend services for development.
- [x] Add a backend `Dockerfile` and frontend `Dockerfile`; install all OS and application dependencies in the appropriate container image.
- [x] Add `.dockerignore` files or a root `.dockerignore` to exclude secrets, Git metadata, local environments, dependency folders, databases and build artifacts from image contexts.
- [x] Bind-mount backend and frontend source directories from the host into their containers for immediate code visibility.
- [x] Configure FastAPI/Uvicorn reload and Vite HMR, with both development servers listening on `0.0.0.0` inside their containers.
- [x] Configure polling-compatible file watching for Docker Desktop on Windows if host filesystem events are not forwarded into the containers.
- [x] Keep Python and Node dependency directories container-managed; do not let source bind mounts replace them with host dependencies.
- [x] Persist the SQLite data directory with a named Docker volume so database data survives container recreation.
- [x] Publish backend port 8000 and frontend port 5173 to the host.
- [x] Configure `.gitignore` to exclude credentials, virtual environments, dependencies, database files and build artifacts.
- [x] Initialize README.md.

### 3.2 Backend Setup

- [x] Use a Python 3.11 backend image; create the virtual environment with uv and install FastAPI, Uvicorn, Pipecat and required provider/transport dependencies inside the container.
- [x] Configure ElevenLabs STT and TTS dependencies.
- [x] Configure Google Gemini dependencies.
- [x] Configure SmallWebRTC transport dependencies.
- [x] Configure Silero VAD dependencies.
- [x] Install environment configuration and focused development dependencies with uv inside the backend container.
- [x] Create `requirements.txt` with compatible, pinned dependency versions.
- [x] Create the FastAPI application entry point.
- [x] Implement `GET /api/health`.
- [x] Configure CORS for local frontend development.

### 3.3 Frontend Setup

- [x] Initialize React with TypeScript and Vite; install frontend dependencies inside the frontend container.
- [x] Configure Tailwind CSS.
- [x] Initialize shadcn/ui.
- [x] Install Lucide React for icons.
- [x] Install Motion for React (formerly Framer Motion) for animations.
- [x] Create the initial application layout.
- [x] Configure the backend API base URL.
- [x] Configure Vite HMR to work through the source bind mount and Docker port mapping.
- [x] Configure polling-compatible file watching for the Windows host bind mount.
- [x] Verify frontend-to-backend connectivity using the health endpoint from the browser (user reports frontend and backend communicate correctly).

### 3.4 Docker Development Workflow

- [x] Document starting the development stack with `docker compose up --build` and stopping it with `docker compose down`.
- [x] Document that source edits are picked up by the running development servers without container restarts.
- [x] Document that dependency, Dockerfile or Compose changes require rebuilding the affected image.
- [x] Ensure the frontend reaches the backend through a browser-accessible host URL; container-only service names must not be used as the browser API hostname.
- [x] Ensure secrets are supplied through ignored local environment files or environment variables and are not copied into images.

### 3.5 Environment Configuration

- [x] Obtain ElevenLabs API credentials.
- [x] Obtain Google Gemini API credentials.
- [x] Select an ElevenLabs voice ID.
- [x] Create backend `.env.example` and frontend `.env.example`; document how local ignored environment files are passed to Compose.
- [x] Validate environment configuration on backend startup.
- [x] Ensure API keys remain exclusively on the backend.

**Backend environment variables:**

```env
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:5173
DATABASE_PATH=/app/data/careline.db
APP_TIMEZONE=Asia/Kolkata
```

**Frontend environment variables:**

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3.6 Project Directory Structure

```text
careline-ai/
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── README.md
├── docs/
│   └── architecture.md
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── voice/
│   │   └── __init__.py
│   ├── database/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   └── routes/
│       └── __init__.py
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   ├── components.json
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── index.css
│   │   ├── lib/
│   │   │   └── utils.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── health.ts
└── Tickets/
    └── Ticket-1.md
```

## 4. API Specification

**Endpoint:** `GET /api/health`

**Expected response:**

```json
{
  "status": "healthy",
  "service": "careline-ai",
  "version": "0.1.0"
}
```

## 5. Acceptance Criteria

- [x] `docker compose up --build` starts the backend on host port 8000 and frontend on host port 5173 (user reports both ports are correct and services are running).
- [x] Python and Node application dependencies are installed and used inside their respective containers, not required on the host (user reports dependencies installed correctly).
- [x] Editing a backend source file is detected by Uvicorn reload without manually restarting the container (user reports reload is working).
- [x] Editing a frontend source file is reflected by Vite HMR without manually restarting the container (user reports verified).
- [x] Frontend container and browser can reach the backend at its configured address (user reports frontend and backend communicate correctly).
- [x] SQLite data volume is created and present (user reported).
- [x] SQLite data remains available after the application containers are recreated (user reports data persisted securely).
- [x] Health endpoint returns HTTP 200 (verified by the reported healthy response).
- [ ] Frontend successfully communicates with the backend.
- [x] All required Python dependencies import without errors (user reports verified).
- [x] Pipecat provider and transport dependencies installed successfully (user reported Python libraries installed correctly).
- [x] Environment variables are loaded correctly (user reported).
- [x] No API credentials are committed to Git (user reported).
- [x] Project follows the defined modular directory structure (user reported).
- [x] README contains Docker-based setup, environment configuration, logs, stop, rebuild and data-persistence instructions (user reported).

## 6. Engineering Guidelines

- Keep the architecture simple, modular and maintainable.
- Use asynchronous Python where required.
- Follow separation of concerns.
- Verify dependency versions against official documentation before installation.
- Avoid deprecated Pipecat APIs.
- Do not implement unnecessary abstractions.
- Use fictional doctors and synthetic patient data.
- Do not implement appointment business logic or the full voice pipeline in this ticket.
- Do not add unrelated features.

## 7. Expected Deliverables

- Initialized full-stack repository.
- Working FastAPI server.
- Working React frontend.
- Verified frontend-backend connectivity.
- Configured development environments.
- Installed and compatible dependencies.
- Secure environment configuration.
- Initial README documentation.

## 8. Definition of Done

The frontend and backend run with Docker Compose, dependencies are installed in their containers, source changes are reflected without manual container restarts, SQLite data persists across container recreation, configuration is secured, and the project is ready for appointment database and voice pipeline implementation.

**Suggested Git commit:**

```text
feat: initialize CareLine AI full-stack project and environment
```
