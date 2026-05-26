from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from auth.jwt import can_access_ticket, get_current_user, require_manager
from database import get_db
from models.activity import TicketActivity
from models.comment import Comment
from models.customer import Customer
from models.notification import NotificationLog
from models.ticket import Ticket
from models.user import User
from schemas.ticket import (
    AISuggestReplyResponse,
    ActivityResponse,
    AssignUpdate,
    CommentCreate,
    CommentResponse,
    StatusUpdate,
    TicketCreate,
    TicketDetailResponse,
    TicketListItem,
    TicketUpdate,
)
from services import gemini_service, telegram_service

router = APIRouter(prefix="/tickets", tags=["tickets"])

VALID_STATUSES = {"open", "in_progress", "resolved", "closed"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}


def _activity(db: Session, ticket_id: int, user_id: int | None, action_type: str, message: str, old=None, new=None):
    item = TicketActivity(
        ticket_id=ticket_id,
        user_id=user_id,
        action_type=action_type,
        message=message,
        old_value=str(old) if old is not None else None,
        new_value=str(new) if new is not None else None,
    )
    db.add(item)
    return item


def _notification(db: Session, ticket_id: int | None, event_type: str, message: str, result: dict):
    log = NotificationLog(
        ticket_id=ticket_id,
        platform="telegram",
        event_type=event_type,
        message=message,
        status=result.get("status", "failed"),
        error_message=result.get("error_message"),
    )
    db.add(log)
    if ticket_id:
        _activity(db, ticket_id, None, "notification", f"Telegram {event_type}: {log.status}")
    return log


def _serialize_comment(c: Comment) -> CommentResponse:
    return CommentResponse(
        id=c.id,
        ticket_id=c.ticket_id,
        user_id=c.user_id,
        user_name=c.user.full_name if c.user else "Unknown",
        body=c.body,
        created_at=c.created_at,
    )


def _serialize_activity(a: TicketActivity) -> ActivityResponse:
    return ActivityResponse(
        id=a.id,
        ticket_id=a.ticket_id,
        user_id=a.user_id,
        user_name=a.user.full_name if a.user else "System",
        action_type=a.action_type,
        message=a.message,
        old_value=a.old_value,
        new_value=a.new_value,
        is_internal=a.is_internal,
        created_at=a.created_at,
    )


def _ticket_list_item(ticket: Ticket) -> TicketListItem:
    return TicketListItem(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        category=ticket.category,
        sentiment=ticket.sentiment,
        customer_id=ticket.customer_id,
        customer_name=ticket.customer.full_name if ticket.customer else "",
        assigned_agent_id=ticket.assigned_agent_id,
        assigned_agent_name=ticket.assigned_agent.full_name if ticket.assigned_agent else None,
        created_at=ticket.created_at,
    )


def _ticket_detail(ticket: Ticket) -> TicketDetailResponse:
    return TicketDetailResponse(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        category=ticket.category,
        sentiment=ticket.sentiment,
        ai_summary=ticket.ai_summary,
        ai_suggested_reply=ticket.ai_suggested_reply,
        customer_id=ticket.customer_id,
        customer_name=ticket.customer.full_name if ticket.customer else "",
        assigned_agent_id=ticket.assigned_agent_id,
        assigned_agent_name=ticket.assigned_agent.full_name if ticket.assigned_agent else None,
        created_at=ticket.created_at,
        resolved_at=ticket.resolved_at,
        comments=[_serialize_comment(c) for c in ticket.comments],
        activities=[_serialize_activity(a) for a in ticket.activities],
    )


def _load_ticket(db: Session, ticket_id: int) -> Ticket:
    ticket = (
        db.query(Ticket)
        .options(
            joinedload(Ticket.customer),
            joinedload(Ticket.assigned_agent),
            joinedload(Ticket.comments).joinedload(Comment.user),
            joinedload(Ticket.activities).joinedload(TicketActivity.user),
        )
        .filter(Ticket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def _ensure_access(user: User, ticket: Ticket):
    if not can_access_ticket(user, ticket):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ticket access denied")


def _handle_resolved(ticket: Ticket, db: Session) -> None:
    comment_bodies = [c.body for c in ticket.comments]
    ticket.ai_summary = gemini_service.generate_summary(ticket.title, ticket.description, comment_bodies)
    ticket.resolved_at = datetime.utcnow()
    _activity(db, ticket.id, None, "ai_update", "AI generated a resolution summary.")
    message = f"Ticket Resolved #{ticket.id}\nTitle: {ticket.title}"
    result = telegram_service.notify_ticket_resolved(ticket.id, ticket.title)
    _notification(db, ticket.id, "resolved", message, result)


@router.get("", response_model=List[TicketListItem])
def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_agent_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Ticket).options(joinedload(Ticket.customer), joinedload(Ticket.assigned_agent))
    if current_user.role != "manager":
        query = query.filter((Ticket.assigned_agent_id == current_user.id) | (Ticket.assigned_agent_id.is_(None)))
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if assigned_agent_id is not None:
        query = query.filter(Ticket.assigned_agent_id == assigned_agent_id)
    if date_from:
        query = query.filter(Ticket.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Ticket.created_at <= datetime.fromisoformat(date_to + " 23:59:59"))
    if search:
        term = f"%{search}%"
        query = query.filter((Ticket.title.ilike(term)) | (Ticket.description.ilike(term)))
    return [_ticket_list_item(t) for t in query.order_by(Ticket.created_at.desc()).all()]


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = _load_ticket(db, ticket_id)
    _ensure_access(current_user, ticket)
    return _ticket_detail(ticket)


@router.post("", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail="Invalid priority")
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if current_user.role != "manager" and data.assigned_agent_id not in (None, current_user.id):
        raise HTTPException(status_code=403, detail="Agents can only create unassigned tickets or assign to themselves")

    ticket = Ticket(
        title=data.title,
        description=data.description,
        customer_id=data.customer_id,
        priority=data.priority,
        assigned_agent_id=data.assigned_agent_id,
        status="open",
        category="general",
        sentiment="neutral",
    )
    db.add(ticket)
    db.flush()
    _activity(db, ticket.id, current_user.id, "created", "Ticket created.")

    ai_result = gemini_service.categorize_and_sentiment(ticket.title, ticket.description)
    ticket.category = ai_result["category"]
    ticket.sentiment = ai_result["sentiment"]
    _activity(db, ticket.id, None, "ai_update", f"AI set category to {ticket.category} and sentiment to {ticket.sentiment}.")

    escalation = gemini_service.escalation_recommendation(ticket.title, ticket.description, ticket.sentiment, ticket.priority)
    if escalation["recommended_priority"] != ticket.priority:
        old_priority = ticket.priority
        ticket.priority = escalation["recommended_priority"]
        _activity(db, ticket.id, None, "priority_change", escalation["reason"] or "AI escalation changed priority.", old_priority, ticket.priority)

    db.commit()
    db.refresh(ticket)

    message = f"New Ticket #{ticket.id}\nTitle: {ticket.title}\nPriority: {ticket.priority}"
    _notification(db, ticket.id, "new_ticket", message, telegram_service.notify_new_ticket(ticket.id, ticket.title, ticket.priority))
    if ticket.priority == "critical":
        critical_message = f"CRITICAL Ticket #{ticket.id}\nTitle: {ticket.title}"
        _notification(db, ticket.id, "critical", critical_message, telegram_service.notify_critical_ticket(ticket.id, ticket.title))
    db.commit()

    return _ticket_detail(_load_ticket(db, ticket.id))


@router.put("/{ticket_id}", response_model=TicketDetailResponse)
def update_ticket(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = _load_ticket(db, ticket_id)
    _ensure_access(current_user, ticket)
    updates = data.model_dump(exclude_unset=True)
    if "assigned_agent_id" in updates and current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can assign tickets")
    if "status" in updates and updates["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    if "priority" in updates and updates["priority"] not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail="Invalid priority")

    old_status = ticket.status
    old_priority = ticket.priority
    old_agent = ticket.assigned_agent_id
    for key, value in updates.items():
        setattr(ticket, key, value)

    if ticket.status != old_status:
        _activity(db, ticket.id, current_user.id, "status_change", "Status changed.", old_status, ticket.status)
    if ticket.priority != old_priority:
        _activity(db, ticket.id, current_user.id, "priority_change", "Priority changed.", old_priority, ticket.priority)
    if ticket.assigned_agent_id != old_agent:
        _activity(db, ticket.id, current_user.id, "assignment_change", "Assigned agent changed.", old_agent, ticket.assigned_agent_id)
    if ticket.status == "resolved" and old_status != "resolved":
        _handle_resolved(ticket, db)
    if ticket.priority == "critical" and old_priority != "critical":
        msg = f"CRITICAL Ticket #{ticket.id}\nTitle: {ticket.title}"
        _notification(db, ticket.id, "critical", msg, telegram_service.notify_critical_ticket(ticket.id, ticket.title))

    db.commit()
    return _ticket_detail(_load_ticket(db, ticket_id))


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db), _: User = Depends(require_manager)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    db.delete(ticket)
    db.commit()


@router.patch("/{ticket_id}/assign", response_model=TicketDetailResponse)
def assign_ticket(ticket_id: int, data: AssignUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_manager)):
    ticket = _load_ticket(db, ticket_id)
    if data.assigned_agent_id:
        agent = db.query(User).filter(User.id == data.assigned_agent_id, User.role == "agent", User.is_active.is_(True)).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Active agent not found")
    old_agent = ticket.assigned_agent_id
    ticket.assigned_agent_id = data.assigned_agent_id
    _activity(db, ticket.id, current_user.id, "assignment_change", "Assigned agent changed.", old_agent, ticket.assigned_agent_id)
    db.commit()
    return _ticket_detail(_load_ticket(db, ticket_id))


@router.patch("/{ticket_id}/status", response_model=TicketDetailResponse)
def update_status(ticket_id: int, data: StatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    ticket = _load_ticket(db, ticket_id)
    _ensure_access(current_user, ticket)
    old_status = ticket.status
    ticket.status = data.status
    if old_status != ticket.status:
        _activity(db, ticket.id, current_user.id, "status_change", "Status changed.", old_status, ticket.status)
    if ticket.status == "resolved" and old_status != "resolved":
        _handle_resolved(ticket, db)
    db.commit()
    return _ticket_detail(_load_ticket(db, ticket_id))


@router.post("/{ticket_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(ticket_id: int, data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    _ensure_access(current_user, ticket)
    comment = Comment(ticket_id=ticket_id, user_id=current_user.id, body=data.body)
    db.add(comment)
    db.flush()
    _activity(db, ticket_id, current_user.id, "comment", data.body)
    db.commit()
    db.refresh(comment)
    return _serialize_comment(comment)


@router.post("/{ticket_id}/ai-suggest-reply", response_model=AISuggestReplyResponse)
def ai_suggest_reply(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = _load_ticket(db, ticket_id)
    _ensure_access(current_user, ticket)
    suggestion = gemini_service.suggest_reply(
        {
            "title": ticket.title,
            "description": ticket.description,
            "customer_name": ticket.customer.full_name if ticket.customer else "Customer",
            "category": ticket.category,
            "sentiment": ticket.sentiment,
            "status": ticket.status,
            "priority": ticket.priority,
        },
        [c.body for c in ticket.comments],
    )
    ticket.ai_suggested_reply = suggestion
    _activity(db, ticket.id, current_user.id, "ai_update", "AI generated a reply suggestion.")
    db.commit()
    return AISuggestReplyResponse(suggestion=suggestion)
