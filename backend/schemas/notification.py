from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationLogResponse(BaseModel):
    id: int
    ticket_id: Optional[int]
    platform: str
    event_type: str
    message: str
    status: str
    error_message: Optional[str]
    sent_at: datetime

    class Config:
        from_attributes = True
