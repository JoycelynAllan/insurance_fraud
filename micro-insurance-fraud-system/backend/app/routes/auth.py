import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
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

# Pydantic validation schemas
class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    branch: str = Field(None, max_length=50)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(body: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new user with standard analyst permissions."""
    clean_email = body.email.strip().lower()
    
    # Check if the user email already exists (case-insensitive)
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
        role="analyst",  # default role for new registrants
        branch=body.branch
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"[DB REGISTER SUCCESS] User '{new_user.email}' (ID: {new_user.id}) inserted and committed successfully.")
        return {"message": "Account created successfully", "user_id": new_user.id}
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


@router.post("/login")
def login_user(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate credentials and generate a session token."""
    # Look up user by email
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate access token containing sub, role, and branch claims
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
            "branch": user.branch
        }
    )
    
    # Expiry calculations
    expiry_time = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    # Store token in active sessions table
    new_session = UserSession(
        user_id=user.id,
        token=access_token,
        expires_at=expiry_time
    )
    db.add(new_session)
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name
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
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "branch": current_user.branch,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }
