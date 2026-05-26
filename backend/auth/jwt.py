"""JWT token creation and FastAPI auth dependencies."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.ticket import Ticket
from models.user import User

ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_manager(user: User = Depends(get_current_user)) -> User:
    if user.role != "manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required")
    return user


def require_agent_or_manager(user: User = Depends(get_current_user)) -> User:
    if user.role not in {"agent", "manager"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent or manager access required")
    return user


def can_access_ticket(user: User, ticket: Ticket) -> bool:
    if user.role == "manager":
        return True
    return ticket.assigned_agent_id in (None, user.id)


def require_ticket_access(ticket_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Ticket:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not can_access_ticket(user, ticket):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ticket access denied")
    return ticket
