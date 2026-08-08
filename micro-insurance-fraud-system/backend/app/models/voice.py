from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from backend.app.db import Base

class VoiceCallLog(Base):
    __tablename__ = "voice_call_logs"

    id = Column(Integer, primary_key=True, index=True)
    customer_phone = Column(String(30), nullable=False, index=True)
    agent_id = Column(String(50), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    outcome = Column(String(30), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    attempt_number = Column(Integer, default=1, nullable=False)
    notes = Column(Text, nullable=True)
