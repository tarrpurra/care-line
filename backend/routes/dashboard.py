from fastapi import APIRouter

from database.schemas import DashboardSummary
from services.appointments import get_dashboard_summary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary():
    return get_dashboard_summary()
