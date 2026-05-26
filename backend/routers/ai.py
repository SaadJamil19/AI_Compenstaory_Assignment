from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.jwt import get_current_user
from models.user import User
from services import gemini_service

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, _: User = Depends(get_current_user)):
    history = [h.model_dump() for h in data.history] if data.history else []
    reply = gemini_service.chat(data.message, history)
    return ChatResponse(reply=reply)
