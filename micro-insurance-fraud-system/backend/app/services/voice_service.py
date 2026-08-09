import os
import uuid
import logging
import requests
from datetime import datetime
from sqlalchemy.orm import Session

from backend.app.db import SessionLocal
from backend.app.models.voice import VoiceCallLog
from backend.app.models.user import User

logger = logging.getLogger(__name__)

# Base audio map for Twi and Dagbani templates
BASE_BACKEND_URL = os.environ.get("BACKEND_PUBLIC_URL", "https://investment-project-3.onrender.com").rstrip("/")
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/JoycelynAllan/insurance_fraud/main/micro-insurance-fraud-system/backend/app/voice/audio"

AUDIO_MAP = {
    "twi": {
        "reminder": os.getenv("TWI_REMINDER_AUDIO_URL", f"{GITHUB_RAW_BASE}/twi_reminder.mp3"),
        "confirm": os.getenv("TWI_CONFIRM_AUDIO_URL", f"{GITHUB_RAW_BASE}/twi_confirm.mp3")
    },
    "dagbani": {
        "reminder": os.getenv("DAGBANI_REMINDER_AUDIO_URL", f"{GITHUB_RAW_BASE}/dagbani_reminder.mp3"),
        "confirm": os.getenv("DAGBANI_CONFIRM_AUDIO_URL", f"{GITHUB_RAW_BASE}/dagbani_confirm.mp3")
    }
}

def get_audio_url(language_pref: str, audio_type: str = "reminder") -> str:
    lang = (language_pref or "twi").lower()
    if lang not in AUDIO_MAP:
        lang = "twi"
    return AUDIO_MAP[lang].get(audio_type, AUDIO_MAP["twi"]["reminder"])

def make_outbound_call(
    customer_phone: str,
    agent_id: str,
    amount: float,
    alert_id: int = None,
    language_pref: str = None
) -> dict:
    """
    Triggers an outbound call via Africa's Talking Voice Gateway.
    """
    db: Session = SessionLocal()
    try:
        # Resolve customer language preference if not provided
        if not language_pref:
            user_rec = db.query(User).filter(
                (User.phone_number == customer_phone) | (User.branch != None)
            ).first()
            if user_rec and hasattr(user_rec, "language_pref") and user_rec.language_pref:
                language_pref = user_rec.language_pref
            else:
                language_pref = "twi"

        at_username = os.environ.get("AT_USERNAME", "sandbox")
        at_api_key = os.environ.get("AT_API_KEY", "")
        at_voice_number = os.environ.get("AT_VOICE_PHONE_NUMBER", "+233200000000")
        
        # Determine AT API endpoint
        if at_username == "sandbox":
            call_url = "https://voice.sandbox.africastalking.com/call"
        else:
            call_url = "https://voice.africastalking.com/call"

        client_request_id = f"REQ-VOICE-{uuid.uuid4().hex[:10]}"
        timestamp = datetime.utcnow()

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "apiKey": at_api_key
        }

        payload = {
            "username": at_username,
            "from": at_voice_number,
            "to": customer_phone,
            "clientRequestId": client_request_id
        }

        outcome = "queued"
        notes = f"[AT Voice Trigger] Dispatched to {customer_phone} (Lang: {language_pref})"

        try:
            response = requests.post(call_url, data=payload, headers=headers, timeout=10)
            logger.info(f"[AT VOICE API] Response status: {response.status_code}, body: {response.text}")
            
            if response.status_code in [200, 201]:
                resp_json = response.json()
                entries = resp_json.get("entries", [])
                if entries:
                    status_text = entries[0].get("status", "Queued")
                    notes = f"[AT Voice Response] Status: {status_text}, RequestId: {client_request_id}"
                    if status_text.lower() in ["queued", "success"]:
                        outcome = "queued"
                    else:
                        outcome = "failed"
            else:
                outcome = "failed"
                notes = f"[AT Voice API Error] HTTP {response.status_code}: {response.text}"
        except Exception as http_err:
            outcome = "failed"
            notes = f"[AT Voice Exception] Network error triggering call: {str(http_err)}"

        # Save call log entry to Supabase PostgreSQL
        call_log = VoiceCallLog(
            customer_phone=customer_phone,
            agent_id=agent_id,
            amount=amount,
            outcome=outcome,
            timestamp=timestamp,
            attempt_number=1,
            notes=notes,
            client_request_id=client_request_id,
            language_pref=language_pref,
            alert_id=alert_id
        )
        db.add(call_log)
        db.commit()
        db.refresh(call_log)

        return {
            "status": "success" if outcome == "queued" else "error",
            "outcome": outcome,
            "notes": notes,
            "client_request_id": client_request_id,
            "language_pref": language_pref,
            "log_id": call_log.id
        }
    except Exception as e:
        logger.error(f"Error in make_outbound_call: {str(e)}", exc_info=True)
        db.rollback()
        return {
            "status": "error",
            "outcome": "failed",
            "notes": f"Internal execution error: {str(e)}"
        }
    finally:
        db.close()
