import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from backend/.env explicitly
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/fraud_db")

# Setup engine with robust pool settings
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
