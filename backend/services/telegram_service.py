"""Telegram Bot API notifications via simple HTTP requests."""
import logging

import requests

from config import settings

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)


def is_configured() -> bool:
    return _is_configured()


def send_message(text: str) -> dict:
    """Send a Telegram message and return a structured result."""
    if not _is_configured():
        logger.debug("Telegram not configured, skipping notification")
        return {"status": "skipped", "error_message": "Telegram is not configured"}
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            error = f"Telegram API error {resp.status_code}: {resp.text}"
            logger.warning(error)
            return {"status": "failed", "error_message": error}
        return {"status": "sent", "error_message": None}
    except Exception as e:
        logger.warning("Telegram send failed: %s", e)
        return {"status": "failed", "error_message": str(e)}


def notify_new_ticket(ticket_id: int, title: str, priority: str) -> dict:
    return send_message(f"New Ticket #{ticket_id}\nTitle: {title}\nPriority: {priority}")


def notify_critical_ticket(ticket_id: int, title: str) -> dict:
    return send_message(f"CRITICAL Ticket #{ticket_id}\nTitle: {title}")


def notify_ticket_resolved(ticket_id: int, title: str) -> dict:
    return send_message(f"Ticket Resolved #{ticket_id}\nTitle: {title}")
