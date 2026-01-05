from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import jwt
from passlib.context import CryptContext

from core.config import settings
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.user_db import UserDB


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(data: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    to_encode = dict(data)
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)




def create_user(db: Session, email: str, password: str, role: str, full_name: str | None = None) -> UserDB:
    email = (email or "").strip().lower()
    role = (role or "").strip()
    full_name = (full_name or "").strip() or None
    password = password or ""

    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    if not password:
        raise HTTPException(status_code=400, detail="password is required")
    if role not in ["Parent", "Teacher", "Admin"]:
        raise HTTPException(status_code=400, detail="role must be Parent/Teacher/Admin")

    exists = db.query(UserDB).filter(UserDB.email == email).first()
    if exists:
        raise HTTPException(status_code=400, detail="User already exists")

    u = UserDB(
        email=email,
        full_name=full_name,
        role=role,
        password_hash=hash_password(password),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u
