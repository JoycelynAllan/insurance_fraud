import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Form, Response, status
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.models.voice import VoiceCallLog
from backend.app.models.alert import FraudAlert
from backend.app.services.voice_service import get_audio_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["Voice Telephony Callback"])

@router.post("/callback")
def handle_voice_callback(
    isActive: str = Form("1"),
    sessionId: str = Form(None),
    direction: str = Form(None),
    callerNumber: str = Form(None),
    destinationNumber: str = Form(None),
    dtmfDigits: str = Form(None),
    recordingUrl: str = Form(None),
    durationInSeconds: int = Form(None),
    currencyCode: str = Form(None),
    amount: float = Form(None),
    clientRequestId: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Single Africa's Talking Voice Callback Endpoint.
    Handles Stage 1 (GetDigits + Audio Play), Stage 2 (DTMF IVR Response), Stage 3 (Call Completion).
    Must return Content-Type: text/plain XML <Response>...</Response>.
    """
    logger.info(
        f"[AT VOICE CALLBACK] isActive={isActive}, sessionId={sessionId}, "
        f"caller={callerNumber}, destination={destinationNumber}, dtmf={dtmfDigits}"
    )

    # Locate existing call log by sessionId, clientRequestId, or phone number
    call_log = None
    if sessionId:
        call_log = db.query(VoiceCallLog).filter(VoiceCallLog.session_id == sessionId).first()
    if not call_log and clientRequestId:
        call_log = db.query(VoiceCallLog).filter(VoiceCallLog.client_request_id == clientRequestId).first()
    if not call_log and (destinationNumber or callerNumber):
        target_phone = destinationNumber if direction == "Outbound" else callerNumber
        call_log = db.query(VoiceCallLog).filter(
            VoiceCallLog.customer_phone == target_phone
        ).order_by(VoiceCallLog.timestamp.desc()).first()

    language_pref = call_log.language_pref if call_log else "twi"

    # Link sessionId to call_log if not already linked
    if call_log and sessionId and not call_log.session_id:
        call_log.session_id = sessionId
        db.commit()

    # STAGE 3: Call Has Ended (isActive == "0")
    if str(isActive) == "0":
        if call_log:
            call_log.duration_seconds = durationInSeconds
            call_log.recording_url = recordingUrl
            call_log.currency_code = currencyCode
            call_log.call_amount = amount
            if not call_log.outcome or call_log.outcome in ["queued", "in_progress"]:
                call_log.outcome = "completed"
            call_log.notes = (call_log.notes or "") + f" | Call ended. Duration: {durationInSeconds}s"
            db.commit()
        xml_response = "<Response/>"
        return Response(content=xml_response, media_type="text/plain")

    # STAGE 2: Customer Pressed DTMF Key
    if dtmfDigits is not None and dtmfDigits != "":
        dtmf_clean = str(dtmfDigits).strip()
        logger.info(f"[AT VOICE IVR] Customer pressed key: {dtmf_clean} for session {sessionId}")

        if call_log:
            call_log.dtmf_digits = dtmf_clean

        if dtmf_clean == "1":
            # Payment Confirmed by Customer
            if call_log:
                call_log.outcome = "payment_confirmed_by_customer"
                call_log.notes = (call_log.notes or "") + " | IVR Key 1 pressed: Payment Confirmed"
                
                # Update associated fraud alert to RESOLVED
                if call_log.alert_id:
                    alert = db.query(FraudAlert).filter(FraudAlert.id == call_log.alert_id).first()
                    if alert:
                        alert.status = "RESOLVED"
                        alert.acknowledged = True
                        alert.acknowledged_at = datetime.utcnow()
                        logger.info(f"[AT VOICE IVR] Updated FraudAlert {alert.id} to RESOLVED via voice keypress 1")
            
            db.commit()

            confirm_audio_url = get_audio_url(language_pref, "confirm")
            xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play url="{confirm_audio_url}"/>
</Response>"""
            return Response(content=xml_response, media_type="text/plain")

        elif dtmf_clean == "2":
            # Customer Requested Transfer to Support
            if call_log:
                call_log.outcome = "transfer_to_support_requested"
                call_log.notes = (call_log.notes or "") + " | IVR Key 2 pressed: Support Transfer Requested"
            db.commit()

            confirm_audio_url = get_audio_url(language_pref, "confirm")
            xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting you to support representative. Please hold.</Say>
</Response>"""
            return Response(content=xml_response, media_type="text/plain")

        else:
            if call_log:
                call_log.notes = (call_log.notes or "") + f" | Invalid IVR Key: {dtmf_clean}"
            db.commit()

            reminder_audio_url = get_audio_url(language_pref, "reminder")
            xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <GetDigits timeout="10" finishOnKey="#">
        <Play url="{reminder_audio_url}"/>
    </GetDigits>
</Response>"""
            return Response(content=xml_response, media_type="text/plain")

    # STAGE 1: Call Just Connected (isActive == "1", no DTMF digits yet)
    if call_log:
        call_log.outcome = "in_progress"
    db.commit()

    reminder_audio_url = get_audio_url(language_pref, "reminder")
    xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <GetDigits timeout="10" finishOnKey="#">
        <Play url="{reminder_audio_url}"/>
    </GetDigits>
</Response>"""
    return Response(content=xml_response, media_type="text/plain")
