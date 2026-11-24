from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="CareLine AI", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "careline-ai", "version": "0.1.0"}
