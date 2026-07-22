from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from backend.app.db import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(10), ForeignKey("agents.agent_id"), nullable=False)
    customer_id = Column(String(10), nullable=False)
    customer_phone = Column(String(20), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    payment_method = Column(String(20), nullable=True)
    remittance_status = Column(String(20), nullable=True)
    branch = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    agent = relationship("Agent", back_populates="transactions")
    features = relationship("TransactionFeature", back_populates="transaction", cascade="all, delete-orphan", uselist=False)


class TransactionFeature(Base):
    __tablename__ = "transaction_features"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    remittance_delay_hours = Column(Integer, default=0, nullable=False)
    cash_ratio = Column(Numeric(6, 4), nullable=True)
    deviation_from_agent_mean = Column(Numeric(10, 2), nullable=True)
    missed_consecutive_count = Column(Integer, default=0, nullable=False)
    is_fraud = Column(Boolean, default=False, nullable=False)
    risk_score = Column(Numeric(5, 2), nullable=True)
    flag_reason = Column(Text, nullable=True)
    scored_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transaction = relationship("Transaction", back_populates="features")
