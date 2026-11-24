from datetime import timedelta

import pytest

from config import settings
from database.models import initialize_database
from database.seed import seed_database


@pytest.fixture
def database(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_path", tmp_path / "careline.db")
    initialize_database()
    seed_database()
    return settings.database_path


@pytest.fixture
def future_slot(database):
    from services.appointments import get_doctor_slots
    from config import settings
    from datetime import datetime
    from zoneinfo import ZoneInfo

    tomorrow = (datetime.now(ZoneInfo(settings.app_timezone)).date() + timedelta(days=1)).isoformat()
    return get_doctor_slots(1, tomorrow)[0]["slot_id"]
