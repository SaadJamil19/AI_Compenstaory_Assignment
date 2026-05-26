from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class TicketActivity(Base):
    __tablename__ = "ticket_activities"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    is_internal = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="activities")
    user = relationship("User", back_populates="activities")
