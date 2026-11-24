from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.models import initialize_database
from database.seed import seed_database
from routes import appointments, dashboard, doctors


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    seed_database()
    yield


app = FastAPI(title="CareLine AI", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(dashboard.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "careline-ai", "version": "0.1.0"}
