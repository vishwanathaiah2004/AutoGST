import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from models.models import User
from models.schemas import AlertResponse, SuccessResponse
from services.auth_service import get_current_user
from services.transaction_service import get_dashboard_stats
from services.alert_service import (
    get_user_alerts, mark_alert_read, mark_all_read, generate_gst_deadline_alerts
)

logger = logging.getLogger("autogst.routes.dashboard")

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
alerts_router = APIRouter(prefix="/alerts", tags=["Alerts"])


@dashboard_router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregated dashboard statistics."""
    logger.info("Dashboard request: user=%d", current_user.id)
    # Generate deadline alerts on dashboard load
    try:
        generate_gst_deadline_alerts(db, current_user.id)
    except Exception:
        pass
    return get_dashboard_stats(db, current_user.id)


# ─── Alerts ──────────────────────────────────────────────────────────────────

@alerts_router.get("", response_model=list)
def list_alerts(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alerts = get_user_alerts(db, current_user.id, unread_only)
    return [
        {
            "id": a.id,
            "title": a.title,
            "message": a.message,
            "severity": a.severity.value,
            "category": a.category,
            "is_read": a.is_read,
            "created_at": str(a.created_at),
        }
        for a in alerts
    ]


@alerts_router.put("/{alert_id}/read", response_model=SuccessResponse)
def read_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mark_alert_read(db, alert_id, current_user.id)
    return SuccessResponse(message="Alert marked as read")


@alerts_router.put("/read-all", response_model=SuccessResponse)
def read_all_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = mark_all_read(db, current_user.id)
    return SuccessResponse(message=f"{count} alerts marked as read")
