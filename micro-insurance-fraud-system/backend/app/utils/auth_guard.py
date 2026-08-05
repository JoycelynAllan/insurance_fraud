import os
import logging
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models.user import User, UserSession

logger = logging.getLogger(__name__)

# Configuration settings using Supabase values
SECRET_KEY = os.getenv("SUPABASE_JWT_SECRET", "0e6ff5e5-bdf3-4557-bb42-1ead4c111f69")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", 8))

import bcrypt

security = HTTPBearer()

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify standard plain text password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generate a JWT token with custom expiry signed with Supabase JWT Secret."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def log_audit_action(user_id: int, method: str, path: str, ip_address: str):
    """Background task to insert audit logs into the database."""
    from backend.app.db import SessionLocal
    from backend.app.models.audit import AuditLog
    
    # Extract agent_id target if present in the endpoint path
    target = None
    path_parts = path.split('/')
    for part in path_parts:
        if part.startswith("AGT"):
            target = part
            break
            
    db = SessionLocal()
    try:
        audit = AuditLog(
            user_id=user_id,
            action=f"{method} {path}",
            target=target,
            detail=None,
            ip_address=ip_address
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to save audit log: {str(e)}")
    finally:
        db.close()

def get_current_user(
    request: Request,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI security dependency to retrieve the current logged-in user.
    Uses Supabase JWT secret. Logs all successful authenticated requests into audit_log.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token using Supabase secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    # Verify session is active in database
    db_session = db.query(UserSession).filter(UserSession.token == token).first()
    if not db_session:
        raise credentials_exception
        
    # Check if session has expired
    if db_session.expires_at < datetime.utcnow():
        db.delete(db_session)
        db.commit()
        raise credentials_exception

    # Retrieve user
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    # Asynchronously log audit action in background tasks
    ip_address = request.client.host if request.client else None
    background_tasks.add_task(
        log_audit_action,
        user_id=user.id,
        method=request.method,
        path=request.url.path,
        ip_address=ip_address
    )
        
    return user
