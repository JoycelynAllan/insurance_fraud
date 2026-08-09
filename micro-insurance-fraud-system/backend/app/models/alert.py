from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from backend.app.db import Base

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(10), ForeignKey("agents.agent_id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True)
    risk_score = Column(Numeric(5, 2), nullable=False)
    flag_reason = Column(Text, nullable=True)
    branch = Column(String(50), nullable=True)
    alerted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    status = Column(String(30), default="PENDING", nullable=False)  # PENDING, INVESTIGATING, RESOLVED

    # Relationships
    agent = relationship("Agent", back_populates="alerts")
    user = relationship("User")
    transaction = relationship("Transaction")
