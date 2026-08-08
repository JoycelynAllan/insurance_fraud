import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from backend/.env explicitly
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("SUPABASE_DATABASE_URL")
    or os.getenv("SUPABASE_POSTGRES_URL")
    or "sqlite:///./fraud_db.db"
)

# Convert Render's legacy postgres:// scheme to postgresql:// required by SQLAlchemy 1.4+
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

import logging

logger = logging.getLogger(__name__)

# Redacted URL logging for startup diagnostics
redacted_url = DATABASE_URL
if "@" in redacted_url:
    prefix, rest = redacted_url.split("@", 1)
    scheme = prefix.split("://")[0] if "://" in prefix else "db"
    redacted_url = f"{scheme}://***:***@{rest}"

logger.warning(f"[DB RUNTIME CONFIG] Resolved Database Connection URL: {redacted_url}")
print(f"[DB RUNTIME CONFIG] Resolved Database Connection URL: {redacted_url}")

# Setup engine with robust pool settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_recycle=300,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
