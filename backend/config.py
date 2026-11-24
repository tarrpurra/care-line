from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    frontend_url: str = "http://localhost:5173"
    database_path: Path = Path("/app/data/careline.db")
    app_timezone: str = "Asia/Kolkata"

    @field_validator("frontend_url")
    @classmethod
    def validate_frontend_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("FRONTEND_URL must be an absolute HTTP(S) URL")
        return value.rstrip("/")

    @field_validator("app_timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("APP_TIMEZONE must be a valid IANA timezone") from exc
        return value


settings = Settings()
