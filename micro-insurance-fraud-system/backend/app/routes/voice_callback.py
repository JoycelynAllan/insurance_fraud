import logging
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db import get_db, SessionLocal
from backend.app.models.voice import VoiceCallLog
from backend.app.models.alert import FraudAlert
from backend.app.models.user import User
from backend.app.utils.auth_guard import get_current_user
from backend.app.services.voice_service import schedule_retry, AUDIO_URLS
from backend.app.routes.alerts import broadcast_alert

logger = logging.getLogger(__name__)
router = APIRouter()

class VoiceTriggerPayload(BaseModel):
    customer_phone: str = Field(..., description="Customer phone number")
    agent_id: str = Field(..., description="Agent ID")
    amount: float = Field(..., description="Amount outstanding")
    language: str = Field("english", description="Preferred language")

@router.post("/voice/callback")
async def voice_callback(
    dtmfDigits: Optional[str] = Form(""),
    callerNumber: Optional[str] = Form(""),
    sessionId: Optional[str] = Form(""),
    isActive: Optional[str] = Form(""),
    language: Optional[str] = Form("english"),
    amount: Optional[str] = Form("150.0")
):
    """
    Public Africa's Talking Voice Callback Endpoint with English, Twi, and Dagbani IVR handling.
    """
    dtmf_val = (dtmfDigits or "").strip()
    lang_val = (language or "english").lower()
    
    print(f"Callback received: dtmfDigits={dtmf_val}, callerNumber={callerNumber}, sessionId={sessionId}, isActive={isActive}, language={lang_val}")

    if dtmf_val == "1":
        # Log payment confirmation and auto-resolve pending alert in Supabase
        db = SessionLocal()
        try:
            call_log = VoiceCallLog(
                customer_phone=callerNumber or "+233200000000",
                agent_id="AGT041",
                amount=float(amount) if amount else 150.0,
                attempt_number=1,
                outcome="payment_confirmed_by_customer",
                called_at=datetime.utcnow(),
                timestamp=datetime.utcnow(),
                language_pref=lang_val,
                dtmf_digits="1"
            )
            db.add(call_log)
            
            # Resolve any PENDING alerts
            pending_alerts = db.query(FraudAlert).filter(FraudAlert.status == "PENDING").all()
            for p_alert in pending_alerts:
                p_alert.status = "RESOLVED"
                p_alert.acknowledged = True
                p_alert.acknowledged_at = datetime.utcnow()
                # Broadcast updated status to WebSocket clients
                await broadcast_alert({
                    "agent_id": str(p_alert.agent_id),
                    "risk_score": float(p_alert.risk_score),
                    "flag_reason": str(p_alert.flag_reason),
                    "status": "RESOLVED",
                    "created_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                })
            db.commit()
        except Exception as e:
            logger.error(f"Failed to auto-resolve alert on DTMF 1: {str(e)}")
            db.rollback()
        finally:
            db.close()

        if lang_val == "twi":
            xml_content = (
                "<Response>\n"
                f'  <Play url="{AUDIO_URLS["twi"]["confirm"]}"/>\n'
                "  <Say>Thank you for confirming. Your payment has been recorded. Goodbye.</Say>\n"
                "</Response>"
            )
        elif lang_val == "dagbani":
            xml_content = (
                "<Response>\n"
                f'  <Play url="{AUDIO_URLS["dagbani"]["confirm"]}"/>\n'
                "  <Say>Thank you for confirming. Your payment has been recorded. Goodbye.</Say>\n"
                "</Response>"
            )
        else: # english
            xml_content = (
                "<Response>\n"
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
        # No DTMF pressed: prompt with language-appropriate audio or Say tag
        if lang_val == "twi":
            xml_content = (
                "<Response>\n"
                f'  <Play url="{AUDIO_URLS["twi"]["reminder"]}"/>\n'
                '  <GetDigits timeout="5" numDigits="1">\n'
                "    <Say>Press 1 to confirm payment. Press 2 for support.</Say>\n"
                "  </GetDigits>\n"
                "</Response>"
            )
        elif lang_val == "dagbani":
            xml_content = (
                "<Response>\n"
                f'  <Play url="{AUDIO_URLS["dagbani"]["reminder"]}"/>\n'
                '  <GetDigits timeout="5" numDigits="1">\n'
                "    <Say>Press 1 to confirm payment. Press 2 for support.</Say>\n"
                "  </GetDigits>\n"
                "</Response>"
            )
        else: # english
            amt_val = amount or "150"
            xml_content = (
                "<Response>\n"
                f"  <Say>Hello. Your MicroInsure Ghana premium payment of {amt_val} Ghana Cedis is outstanding. Please contact your agent. Press 1 if you have already paid. Press 2 to speak to support.</Say>\n"
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
    language = body.language or "english"

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
    return {
        "total": len(logs_list),
        "limit": len(logs_list),
        "offset": 0,
        "logs": logs_list
    }
