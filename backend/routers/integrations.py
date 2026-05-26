from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.jwt import require_manager
from database import get_db
from models.notification import NotificationLog
from models.user import User
from services import gemini_service, telegram_service

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/health")
def integration_health(_: User = Depends(require_manager)):
    return {
        "gemini": {
            "configured": gemini_service.is_configured(),
            "status": "configured" if gemini_service.is_configured() else "missing",
        },
        "telegram": {
            "configured": telegram_service.is_configured(),
            "status": "configured" if telegram_service.is_configured() else "missing",
        },
    }


@router.post("/gemini-test")
def gemini_test(_: User = Depends(require_manager)):
    result = gemini_service.test_categorization()
    return {
        "configured": gemini_service.is_configured(),
        "category": result["category"],
        "sentiment": result["sentiment"],
        "note": "Fallback output was used because GEMINI_API_KEY is missing."
        if not gemini_service.is_configured()
        else "Gemini request completed or returned validated output.",
    }


@router.post("/telegram-test")
def telegram_test(db: Session = Depends(get_db), _: User = Depends(require_manager)):
    message = "AI CRM integration health check: Telegram test message"
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
    return {
        "configured": telegram_service.is_configured(),
        "status": log.status,
        "error_message": log.error_message,
        "notification_log_id": log.id,
    }
