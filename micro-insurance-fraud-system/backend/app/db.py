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

def auto_migrate_schema():
    """Idempotently adds missing columns to pre-existing PostgreSQL tables on Supabase."""
    if engine.dialect.name == "postgresql":
        try:
            from sqlalchemy import text
            with engine.begin() as conn:
                # Users table schema
                conn.execute(text("ALTER TABLE public.users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(30);"))
                conn.execute(text("ALTER TABLE public.users ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN DEFAULT FALSE;"))
                conn.execute(text("ALTER TABLE public.users ADD COLUMN IF NOT EXISTS branch VARCHAR(50);"))
                conn.execute(text("ALTER TABLE public.users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;"))

                # Voice Call Logs table schema
                conn.execute(text("ALTER TABLE public.voice_call_logs ADD COLUMN IF NOT EXISTS session_id VARCHAR(100);"))
                conn.execute(text("ALTER TABLE public.voice_call_logs ADD COLUMN IF NOT EXISTS client_request_id VARCHAR(100);"))
                conn.execute(text("ALTER TABLE public.voice_call_logs ADD COLUMN IF NOT EXISTS language_pref VARCHAR(20) DEFAULT 'twi';"))
                conn.execute(text("ALTER TABLE public.voice_call_logs ADD COLUMN IF NOT EXISTS dtmf_digits VARCHAR(10);"))
                conn.execute(text("ALTER TABLE public.voice_call_logs ADD COLUMN IF NOT EXISTS recording_url TEXT;"))
                conn.execute(text("ALTER TABLE public.voice_call_logs ADD COLUMN IF NOT EXISTS duration_seconds INTEGER;"))
                conn.execute(text("ALTER TABLE public.voice_call_logs ADD COLUMN IF NOT EXISTS currency_code VARCHAR(10);"))
                conn.execute(text("ALTER TABLE public.voice_call_logs ADD COLUMN IF NOT EXISTS call_amount FLOAT;"))
                conn.execute(text("ALTER TABLE public.voice_call_logs ADD COLUMN IF NOT EXISTS alert_id INTEGER;"))

                # Fraud Alerts table schema
                conn.execute(text("ALTER TABLE public.fraud_alerts ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'PENDING';"))
                conn.execute(text("ALTER TABLE public.fraud_alerts ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMP;"))

            logger.info("[DB SCHEMA SYNC] Successfully verified/updated database table schemas in Supabase PostgreSQL.")
        except Exception as e:
            logger.warning(f"[DB SCHEMA SYNC] Table schema verification warning: {str(e)}")
