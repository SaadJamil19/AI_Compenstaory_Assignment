from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.jwt import get_current_user, require_manager
from auth.password import hash_password
from database import get_db
from models.user import User
from schemas.auth import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

VALID_ROLES = {"agent", "manager"}


@router.get("/agents", response_model=List[UserResponse])
def list_agents(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    agents = db.query(User).filter(User.role == "agent", User.is_active.is_(True)).order_by(User.full_name).all()
    return [UserResponse.model_validate(a) for a in agents]


@router.get("", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_manager)):
    return [UserResponse.model_validate(u) for u in db.query(User).order_by(User.created_at.desc()).all()]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_manager)):
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(email=data.email, full_name=data.full_name, role=data.role, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_manager)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updates = data.model_dump(exclude_unset=True)
    if "role" in updates and updates["role"] not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    if "email" in updates and updates["email"] != user.email and db.query(User).filter(User.email == updates["email"]).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    password = updates.pop("password", None)
    if password:
        user.hashed_password = hash_password(password)
    for key, value in updates.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/active", response_model=UserResponse)
def set_active(user_id: int, is_active: bool, db: Session = Depends(get_db), current_user: User = Depends(require_manager)):
    if current_user.id == user_id and not is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate yourself")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
