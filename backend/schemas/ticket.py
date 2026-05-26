from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TicketCreate(BaseModel):
    title: str
    description: str
    customer_id: int
    priority: str = "medium"
    assigned_agent_id: Optional[int] = None


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    assigned_agent_id: Optional[int] = None


class StatusUpdate(BaseModel):
    status: str


class AssignUpdate(BaseModel):
    assigned_agent_id: Optional[int] = None


class CommentCreate(BaseModel):
    body: str


class CommentResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    user_name: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: Optional[int]
    user_name: Optional[str]
    action_type: str
    message: str
    old_value: Optional[str]
    new_value: Optional[str]
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TicketListItem(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    category: str
    sentiment: str
    customer_id: int
    customer_name: str
    assigned_agent_id: Optional[int]
    assigned_agent_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TicketDetailResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    category: str
    sentiment: str
    ai_summary: Optional[str]
    ai_suggested_reply: Optional[str]
    customer_id: int
    customer_name: str
    assigned_agent_id: Optional[int]
    assigned_agent_name: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    comments: List[CommentResponse] = []
    activities: List[ActivityResponse] = []

    class Config:
        from_attributes = True


class AISuggestReplyResponse(BaseModel):
    suggestion: str
