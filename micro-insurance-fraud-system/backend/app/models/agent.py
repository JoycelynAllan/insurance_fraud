from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from backend.app.db import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(10), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    branch = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transactions = relationship("Transaction", back_populates="agent", cascade="all, delete-orphan")
    alerts = relationship("FraudAlert", back_populates="agent", cascade="all, delete-orphan")
