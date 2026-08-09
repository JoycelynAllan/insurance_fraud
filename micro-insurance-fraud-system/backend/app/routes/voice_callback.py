import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.models.voice import VoiceCallLog
from backend.app.models.user import User
from backend.app.utils.auth_guard import get_current_user
from backend.app.services.voice_service import schedule_retry, AUDIO_URLS

logger = logging.getLogger(__name__)
router = APIRouter()

class VoiceTriggerPayload(BaseModel):
    customer_phone: str = Field(..., description="Customer phone number")
    agent_id: str = Field(..., description="Agent ID")
    amount: float = Field(..., description="Amount outstanding")
    language: str = Field("twi", description="Preferred language")

@router.post("/voice/callback")
def voice_callback(
    dtmfDigits: Optional[str] = Form(""),
    callerNumber: Optional[str] = Form(""),
    sessionId: Optional[str] = Form(""),
    isActive: Optional[str] = Form(""),
    language: Optional[str] = Form("twi")
):
    """
    Public Africa's Talking Voice Callback Endpoint.
    """
    dtmf_val = (dtmfDigits or "").strip()
    lang_val = (language or "twi").lower()
    
    print(f"Callback received: dtmfDigits={dtmf_val}, callerNumber={callerNumber}, sessionId={sessionId}, isActive={isActive}, language={lang_val}")

    lang_dict = AUDIO_URLS.get(lang_val, AUDIO_URLS["twi"])
    rem_url = lang_dict.get("reminder", AUDIO_URLS["twi"]["reminder"])
    conf_url = lang_dict.get("confirm", AUDIO_URLS["twi"]["confirm"])

    if dtmf_val == "1":
        xml_content = (
            "<Response>\n"
            f'  <Play url="{conf_url}"/>\n'
            "  <Say>Thank you for confirming. Your payment has been recorded. Goodbye.</Say>\n"
            "</Response>"
        )
        return PlainTextResponse(content=xml_content, media_type="application/xml")
    elif dtmf_val == "2":
        xml_content = (
            "<Response>\n"
            "  <Say>Please hold. A support agent will contact you shortly. Goodbye.</Say>\n"
            "</Response>"
        )
        return PlainTextResponse(content=xml_content, media_type="application/xml")
    else:
        xml_content = (
            "<Response>\n"
            f'  <Play url="{rem_url}"/>\n'
            '  <GetDigits timeout="5" numDigits="1">\n'
            "    <Say>Press 1 to confirm payment. Press 2 for support.</Say>\n"
            "  </GetDigits>\n"
            "</Response>"
        )
        return PlainTextResponse(content=xml_content, media_type="application/xml")

@router.post("/voice/trigger")
def trigger_voice_reminder(
    body: VoiceTriggerPayload,
    current_user: User = Depends(get_current_user)
):
    """
    Protected endpoint to trigger payment reminder retry schedule.
    """
    customer_phone = body.customer_phone
    agent_id = body.agent_id
    amount = body.amount
    language = body.language or "twi"

    schedule_retry(customer_phone, agent_id, amount, language, attempt=1)
    return {"status": "call scheduled", "phone": customer_phone, "attempt": 1}

@router.get("/voice/logs")
def get_voice_logs_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Protected endpoint to query all voice call logs from public.voice_call_logs.
    """
    logs_records = db.query(VoiceCallLog).order_by(VoiceCallLog.called_at.desc()).all()
    logs_list = []
    for r in logs_records:
        logs_list.append({
            "id": r.id,
            "customer_phone": r.customer_phone,
            "agent_id": r.agent_id,
            "amount": float(r.amount),
            "attempt_number": r.attempt_number,
            "outcome": r.outcome,
            "called_at": r.called_at.isoformat() + "Z" if r.called_at else (r.timestamp.isoformat() + "Z" if r.timestamp else None),
            "timestamp": r.timestamp.isoformat() + "Z" if r.timestamp else None,
            "notes": r.notes,
            "session_id": r.session_id,
            "language_pref": r.language_pref,
            "dtmf_digits": r.dtmf_digits
        })
    return logs_list
