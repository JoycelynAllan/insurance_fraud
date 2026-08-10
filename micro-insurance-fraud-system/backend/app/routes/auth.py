import logging
import uuid
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models.user import User, UserSession
from backend.app.utils.auth_guard import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_HOURS,
    security
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

VALID_BRANCHES = {"Accra", "Kumasi", "Tamale", "Takoradi", "Cape_Coast"}

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    branch: str = Field(..., description="Branch office name")
    role: Optional[str] = Field("supervisor")

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: str) -> str:
        if v not in VALID_BRANCHES:
            raise ValueError(f"Branch must be one of: {', '.join(VALID_BRANCHES)}")
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(body: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new supervisor account. Field agents do not have system access."""
    clean_role = (body.role or "supervisor").strip().lower()
    if clean_role != "supervisor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only supervisors can register on this platform. Field agents do not have system access."
        )

    clean_email = body.email.strip().lower()

    # Check if user email already exists
    existing_user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = User(
        full_name=body.full_name.strip(),
        email=clean_email,
        password_hash=hash_password(body.password),
        role="supervisor",
        branch=body.branch,
        language_pref="english"
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create session token
        access_token = create_access_token(
            data={
                "sub": str(new_user.id),
                "email": new_user.email,
                "role": "supervisor",
                "branch": new_user.branch,
                "full_name": new_user.full_name,
                "nonce": str(uuid.uuid4())
            }
        )

        expiry_time = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        new_session = UserSession(
            user_id=new_user.id,
            token=access_token,
            expires_at=expiry_time
        )
        db.add(new_session)
        db.commit()

        logger.info(f"[REGISTER SUCCESS] Supervisor '{new_user.email}' (ID: {new_user.id}) created.")
        return {
            "message": "Account created successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": new_user.id,
            "role": "supervisor",
            "branch": new_user.branch,
            "full_name": new_user.full_name
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

@router.post("/login")
def login_user(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate credentials for supervisor users."""
    user = db.query(User).filter(func.lower(User.email) == body.email.strip().lower()).first()

    # Reject field agent / risk officer logins with 403 Forbidden
    if user and user.role in ["agent", "risk_officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Field agents do not have access to this system."
        )

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Clear old sessions
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "branch": user.branch,
            "full_name": user.full_name,
            "nonce": str(uuid.uuid4())
        }
    )

    expiry_time = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    new_session = UserSession(
        user_id=user.id,
        token=access_token,
        expires_at=expiry_time
    )
    db.add(new_session)
    user.last_login = datetime.utcnow()
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
        "branch": user.branch
    }

@router.post("/logout")
def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    token = credentials.credentials
    db_session = db.query(UserSession).filter(UserSession.token == token).first()
    if db_session:
        db.delete(db_session)
        db.commit()
    return {"message": "Logged out successfully"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "branch": current_user.branch,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }
