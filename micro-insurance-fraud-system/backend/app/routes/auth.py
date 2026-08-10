import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

VALID_ROLES = {"supervisor", "agent"}
VALID_BRANCHES = {"Accra", "Kumasi", "Tamale", "Takoradi", "Cape_Coast"}
VALID_LANGUAGES = {"twi", "dagbani", "english"}

# Pydantic validation schemas
class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(..., description="Must be 'supervisor' or 'agent'")
    branch: Optional[str] = Field(None, max_length=50)
    language_pref: Optional[str] = Field("english")
    agent_id: Optional[str] = Field(None)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v_clean = (v or "").strip().lower()
        if v_clean not in VALID_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(VALID_ROLES)}")
        return v_clean

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: Optional[str]) -> Optional[str]:
        if v:
            if v not in VALID_BRANCHES:
                raise ValueError(f"Branch must be one of: {', '.join(VALID_BRANCHES)}")
        return v

    @field_validator("language_pref")
    @classmethod
    def validate_lang(cls, v: Optional[str]) -> str:
        v_clean = (v or "english").strip().lower()
        if v_clean not in VALID_LANGUAGES:
            raise ValueError(f"language_pref must be one of: {', '.join(VALID_LANGUAGES)}")
        return v_clean

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(body: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new user with supervisor or agent role."""
    clean_email = body.email.strip().lower()
    
    # Require branch for agents
    if body.role == "agent" and not body.branch:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Branch is required when registering as a Field Agent."
        )

    # Check if the user email already exists (case-insensitive)
    existing_user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    assigned_agent_id = body.agent_id
    if body.role == "agent" and not assigned_agent_id:
        assigned_agent_id = "AGT041" # default agent mapping if not specified

    new_user = User(
        full_name=body.full_name.strip(),
        email=clean_email,
        password_hash=hash_password(body.password),
        role=body.role,
        branch=body.branch,
        language_pref=body.language_pref,
        agent_id=assigned_agent_id
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"[DB REGISTER SUCCESS] User '{new_user.email}' (ID: {new_user.id}, Role: {new_user.role}) inserted successfully.")
        return {"message": "Account created successfully", "user_id": new_user.id, "role": new_user.role}
    except IntegrityError as ie:
        db.rollback()
        err_msg = str(ie)
        logger.warning(f"[DB REGISTER DUPLICATE] Unique constraint violation for email '{clean_email}': {err_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except Exception as exc:
        db.rollback()
        err_msg = str(exc)
        logger.error(f"[DB REGISTER EXCEPTION] Failed to commit new user '{clean_email}': {err_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database commit error: {err_msg}"
        )

import uuid

@router.post("/login")
def login_user(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate credentials and generate a session token with role claims."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Clear old sessions for this user to avoid token conflicts
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    
    # Generate access token containing sub, role, branch, language_pref, and unique nonce claims
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
            "branch": user.branch,
            "language_pref": user.language_pref or "english",
            "agent_id": user.agent_id,
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
        "branch": user.branch,
        "language_pref": user.language_pref or "english",
        "agent_id": user.agent_id
    }

@router.post("/logout")
def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Invalidate current user session by deleting token from database."""
    token = credentials.credentials
    db_session = db.query(UserSession).filter(UserSession.token == token).first()
    if db_session:
        db.delete(db_session)
        db.commit()
    return {"message": "Logged out successfully"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Return user context for the active session."""
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "branch": current_user.branch,
        "language_pref": current_user.language_pref or "english",
        "agent_id": current_user.agent_id,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }
