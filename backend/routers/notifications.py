from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.jwt import require_manager
from database import get_db
from models.notification import NotificationLog
from models.user import User
from schemas.notification import NotificationLogResponse
from services import telegram_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationLogResponse])
def list_notifications(db: Session = Depends(get_db), _: User = Depends(require_manager)):
    logs = db.query(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(100).all()
    return [NotificationLogResponse.model_validate(log) for log in logs]


@router.post("/test", response_model=NotificationLogResponse)
def send_test_notification(db: Session = Depends(get_db), _: User = Depends(require_manager)):
    message = "AI CRM test Telegram notification"
    result = telegram_service.send_message(message)
    log = NotificationLog(
        ticket_id=None,
        platform="telegram",
        event_type="test",
        message=message,
        status=result.get("status", "failed"),
        error_message=result.get("error_message"),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return NotificationLogResponse.model_validate(log)
