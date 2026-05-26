from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth.jwt import require_manager
from database import get_db
from models.ticket import Ticket
from models.user import User

router = APIRouter(prefix="/reports", tags=["reports"])


def _group(db: Session, field) -> dict:
    return {str(k or "unknown"): v for k, v in db.query(field, func.count(Ticket.id)).group_by(field).all()}


@router.get("/summary")
def summary(db: Session = Depends(get_db), _: User = Depends(require_manager)):
    resolved = db.query(Ticket).filter(Ticket.resolved_at.isnot(None)).all()
    hours = [
        (t.resolved_at - t.created_at).total_seconds() / 3600
        for t in resolved
        if t.resolved_at and t.created_at
    ]
    agents = db.query(User).filter(User.role == "agent").all()
    performance = []
    for agent in agents:
        assigned = db.query(Ticket).filter(Ticket.assigned_agent_id == agent.id)
        performance.append(
            {
                "agent_id": agent.id,
                "agent_name": agent.full_name,
                "assigned_total": assigned.count(),
                "resolved_total": assigned.filter(Ticket.status.in_(["resolved", "closed"])).count(),
            }
        )
    recent = db.query(Ticket).filter(Ticket.status == "resolved").order_by(Ticket.resolved_at.desc()).limit(10).all()
    return {
        "tickets_by_category": _group(db, Ticket.category),
        "tickets_by_status": _group(db, Ticket.status),
        "tickets_by_priority": _group(db, Ticket.priority),
        "agent_performance": performance,
        "average_resolution_hours": round(sum(hours) / len(hours), 2) if hours else 0,
        "recent_resolved_tickets": [
            {"id": t.id, "title": t.title, "resolved_at": t.resolved_at or datetime.utcnow()}
            for t in recent
        ],
    }
