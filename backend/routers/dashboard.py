from datetime import date, datetime, time

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth.jwt import get_current_user
from database import get_db
from models.ticket import Ticket
from models.user import User
from schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _counts(query, field) -> dict:
    return {str(k or "unknown"): v for k, v in query.with_entities(field, func.count(Ticket.id)).group_by(field).all()}


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    base = db.query(Ticket)
    if current_user.role != "manager":
        base = base.filter(Ticket.assigned_agent_id == current_user.id)

    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    total = base.count()
    open_count = base.filter(Ticket.status == "open").count()
    in_progress = base.filter(Ticket.status == "in_progress").count()
    resolved_today = base.filter(Ticket.status == "resolved", Ticket.resolved_at >= today_start, Ticket.resolved_at <= today_end).count()
    critical = base.filter(Ticket.priority == "critical").count()
    unassigned = db.query(Ticket).filter(Ticket.assigned_agent_id.is_(None)).count() if current_user.role == "manager" else 0

    agent_workloads = []
    if current_user.role == "manager":
        agents = db.query(User).filter(User.role == "agent", User.is_active.is_(True)).order_by(User.full_name).all()
        for agent in agents:
            q = db.query(Ticket).filter(Ticket.assigned_agent_id == agent.id)
            agent_workloads.append(
                {
                    "agent_id": agent.id,
                    "agent_name": agent.full_name,
                    "open_count": q.filter(Ticket.status == "open").count(),
                    "in_progress_count": q.filter(Ticket.status == "in_progress").count(),
                    "critical_count": q.filter(Ticket.priority == "critical").count(),
                    "total_assigned": q.count(),
                }
            )

    my_assigned = []
    if current_user.role == "agent":
        tickets = (
            db.query(Ticket)
            .filter(Ticket.assigned_agent_id == current_user.id, Ticket.status.in_(["open", "in_progress"]))
            .order_by(Ticket.priority.desc(), Ticket.created_at.desc())
            .limit(10)
            .all()
        )
        my_assigned = [
            {"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "created_at": t.created_at}
            for t in tickets
        ]

    return DashboardStats(
        total_tickets=total,
        open_tickets=open_count,
        in_progress_tickets=in_progress,
        resolved_today=resolved_today,
        critical_tickets=critical,
        unassigned_tickets=unassigned,
        tickets_by_status=_counts(base, Ticket.status),
        tickets_by_priority=_counts(base, Ticket.priority),
        tickets_by_category=_counts(base, Ticket.category),
        agent_workloads=agent_workloads,
        my_assigned_tickets=my_assigned,
    )
