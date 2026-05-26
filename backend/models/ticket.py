from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="open", nullable=False)
    priority = Column(String(50), default="medium", nullable=False)
    category = Column(String(50), default="general", nullable=False)
    sentiment = Column(String(50), default="neutral", nullable=False)
    ai_summary = Column(Text, nullable=True)
    ai_suggested_reply = Column(Text, nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="tickets")
    assigned_agent = relationship("User", back_populates="assigned_tickets", foreign_keys=[assigned_agent_id])
    comments = relationship("Comment", back_populates="ticket", order_by="Comment.created_at", cascade="all, delete-orphan")
    activities = relationship("TicketActivity", back_populates="ticket", order_by="TicketActivity.created_at", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="ticket")
