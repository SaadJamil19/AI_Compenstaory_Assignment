from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="agent")  # agent | manager
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assigned_tickets = relationship("Ticket", back_populates="assigned_agent", foreign_keys="Ticket.assigned_agent_id")
    comments = relationship("Comment", back_populates="user")
    activities = relationship("TicketActivity", back_populates="user")
