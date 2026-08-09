from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from backend.app.db import Base

class VoiceCallLog(Base):
    __tablename__ = "voice_call_logs"

    id = Column(Integer, primary_key=True, index=True)
    customer_phone = Column(String(30), nullable=False, index=True)
    agent_id = Column(String(50), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    outcome = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    attempt_number = Column(Integer, default=1, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Africa's Talking Voice session & IVR fields
    session_id = Column(String(100), nullable=True, index=True)
    client_request_id = Column(String(100), nullable=True, index=True)
    language_pref = Column(String(20), default="twi", nullable=False)
    dtmf_digits = Column(String(10), nullable=True)
    recording_url = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    currency_code = Column(String(10), nullable=True)
    call_amount = Column(Float, nullable=True)
    alert_id = Column(Integer, nullable=True)
