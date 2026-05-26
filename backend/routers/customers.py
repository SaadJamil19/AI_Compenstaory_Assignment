from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.jwt import get_current_user, require_manager
from database import get_db
from models.activity import TicketActivity
from models.comment import Comment
from models.customer import Customer
from models.ticket import Ticket
from models.user import User
from schemas.customer import CustomerCreate, CustomerProfile, CustomerResponse, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=List[CustomerResponse])
def list_customers(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Customer)
    if search:
        term = f"%{search}%"
        query = query.filter(
            (Customer.full_name.ilike(term))
            | (Customer.email.ilike(term))
            | (Customer.company.ilike(term))
        )
    return query.order_by(Customer.created_at.desc()).all()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}/profile", response_model=CustomerProfile)
def get_customer_profile(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    tickets = db.query(Ticket).filter(Ticket.customer_id == customer_id).order_by(Ticket.created_at.desc()).all()
    ticket_ids = [t.id for t in tickets]
    activities = []
    if ticket_ids:
        activities = (
            db.query(TicketActivity)
            .filter(TicketActivity.ticket_id.in_(ticket_ids))
            .order_by(TicketActivity.created_at.desc())
            .all()
        )
    history = [
        {
            "id": a.id,
            "ticket_id": a.ticket_id,
            "ticket_title": next((t.title for t in tickets if t.id == a.ticket_id), ""),
            "action_type": a.action_type,
            "message": a.message,
            "old_value": a.old_value,
            "new_value": a.new_value,
            "author": a.user.full_name if a.user else "System",
            "created_at": a.created_at,
        }
        for a in activities
    ]
    latest_ticket = tickets[0] if tickets else None
    return {
        "customer": customer,
        "tickets": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "category": t.category,
                "sentiment": t.sentiment,
                "assigned_agent_name": t.assigned_agent.full_name if t.assigned_agent else None,
                "created_at": t.created_at,
                "resolved_at": t.resolved_at,
            }
            for t in tickets
        ],
        "communication_history": history,
        "latest_ticket": {
            "id": latest_ticket.id,
            "status": latest_ticket.status,
            "priority": latest_ticket.priority,
            "category": latest_ticket.category,
            "sentiment": latest_ticket.sentiment,
        }
        if latest_ticket
        else None,
    }


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_manager),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(customer)
    db.commit()
