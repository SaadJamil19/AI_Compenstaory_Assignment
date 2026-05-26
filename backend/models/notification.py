from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True, index=True)
    platform = Column(String(50), default="telegram", nullable=False)
    event_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="notifications")
