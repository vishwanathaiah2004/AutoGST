import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.models import Alert, AlertSeverity

logger = logging.getLogger("autogst.alerts")


def create_alert(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    severity: str = "info",
    category: Optional[str] = None,
    related_transaction_id: Optional[int] = None,
    metadata: Optional[dict] = None,
) -> Alert:
    """Create a new alert for a user."""
    try:
        alert = Alert(
            user_id=user_id,
            title=title,
            message=message,
            severity=AlertSeverity(severity),
            category=category,
            related_transaction_id=related_transaction_id,
            alert_metadata=metadata,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        logger.info("Alert created: user=%d severity=%s title='%s'", user_id, severity, title)
        return alert
    except Exception as e:
        db.rollback()
        logger.error("Failed to create alert: %s", str(e))
        raise


def get_user_alerts(
    db: Session, user_id: int, unread_only: bool = False, limit: int = 50
) -> List[Alert]:
    query = db.query(Alert).filter(Alert.user_id == user_id)
    if unread_only:
        query = query.filter(Alert.is_read == False)
    return query.order_by(Alert.created_at.desc()).limit(limit).all()


def mark_alert_read(db: Session, alert_id: int, user_id: int) -> Alert:
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert


def mark_all_read(db: Session, user_id: int) -> int:
    count = db.query(Alert).filter(Alert.user_id == user_id, Alert.is_read == False).count()
    db.query(Alert).filter(Alert.user_id == user_id, Alert.is_read == False).update({"is_read": True})
    db.commit()
    return count


def generate_gst_deadline_alerts(db: Session, user_id: int) -> None:
    """Generate GST filing deadline reminders."""
    from datetime import date
    today = date.today()

    # GSTR-1 due on 11th of next month
    if today.day >= 5 and today.day <= 11:
        create_alert(
            db=db,
            user_id=user_id,
            title="GSTR-1 Filing Reminder",
            message=f"GSTR-1 for last month is due on the 11th. Please review and file your returns.",
            severity="warning",
            category="gst",
        )

    # GSTR-3B due on 20th
    if today.day >= 15 and today.day <= 20:
        create_alert(
            db=db,
            user_id=user_id,
            title="GSTR-3B Filing Reminder",
            message=f"GSTR-3B for last month is due on the 20th. Ensure your tax payment is ready.",
            severity="critical",
            category="gst",
        )
