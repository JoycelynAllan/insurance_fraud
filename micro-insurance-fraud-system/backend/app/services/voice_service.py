import os
import uuid
import logging
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import africastalking

from backend.app.db import SessionLocal
from backend.app.models.voice import VoiceCallLog
from backend.app.models.user import User

logger = logging.getLogger(__name__)

# Read AT credentials from environment
AT_USERNAME = os.environ.get("AT_USERNAME", "sandbox")
AT_API_KEY = os.environ.get("AT_API_KEY", "")

# Initialize Africa's Talking SMS & APScheduler
africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms = africastalking.SMS

scheduler = BackgroundScheduler()
scheduler.start()

AUDIO_URLS = {
    "twi": {
        "reminder": "https://xvykfctqxsnttiibxvyu.supabase.co/storage/v1/object/public/audio/twi_reminder.mp3",
        "confirm": "https://xvykfctqxsnttiibxvyu.supabase.co/storage/v1/object/public/audio/twi_confirm.mp3"
    },
    "dagbani": {
        "reminder": "https://xvykfctqxsnttiibxvyu.supabase.co/storage/v1/object/public/audio/dagbani_reminder.mp3",
        "confirm": "https://xvykfctqxsnttiibxvyu.supabase.co/storage/v1/object/public/audio/dagbani_confirm.mp3"
    }
}

def send_payment_reminder(customer_phone: str, agent_id: str, amount: float, language: str = "twi", attempt: int = 1) -> str:
    """
    Sends localized payment reminder SMS via Africa's Talking.
    """
    lang = (language or "twi").lower()
    if lang == "twi":
        message = f"MicroInsure Ghana: Wo insurance premium a GHS {amount} nte ho. Fa sika no ko wo agent {agent_id} nkyen."
    elif lang == "dagbani":
        message = f"MicroInsure Ghana: A insurance puuni GHS {amount} bi ka. Sheri ni fo agent {agent_id} ka amoonin."
    else:
        message = f"MicroInsure Ghana: Your insurance premium of GHS {amount} is outstanding. Please contact agent {agent_id}."

    try:
        response = sms.send(message=message, recipients=[customer_phone])
        logger.info(f"[AT SMS API] Response: {response}")
        outcome = "sent"
    except Exception as e:
        logger.error(f"[AT SMS EXCEPTION] {str(e)}")
        outcome = f"failed: {str(e)}"

    print(f"[Attempt {attempt}] SMS to {customer_phone}: {outcome}")
    log_voice_attempt(customer_phone, agent_id, amount, attempt, outcome)
    return outcome

def log_voice_attempt(customer_phone: str, agent_id: str, amount: float, attempt: int, outcome: str):
    """
    Logs voice/SMS attempt into public.voice_call_logs using SQLAlchemy Session.
    """
    db = SessionLocal()
    try:
        now = datetime.now()
        call_log = VoiceCallLog(
            customer_phone=customer_phone,
            agent_id=agent_id,
            amount=float(amount),
            attempt_number=attempt,
            outcome=str(outcome),
            called_at=now,
            timestamp=now,
            language_pref="twi"
        )
        db.add(call_log)
        db.commit()
        print(f"Log voice attempt saved to DB for {customer_phone}")
    except Exception as db_err:
        logger.error(f"Failed to log voice attempt: {str(db_err)}")
        db.rollback()
    finally:
        db.close()

def schedule_retry(customer_phone: str, agent_id: str, amount: float, language: str = "twi", attempt: int = 1):
    """
    Schedules payment reminder attempt with exponential delay (0, 2h, 4h).
    """
    if attempt > 3:
        print(f"Max retries reached for {customer_phone}")
        return

    delay_hours = [0, 2, 4][attempt - 1]
    run_time = datetime.now() + timedelta(hours=delay_hours)

    if attempt == 1:
        send_payment_reminder(customer_phone, agent_id, amount, language, attempt)

    if attempt < 3:
        scheduler.add_job(
            func=send_payment_reminder,
            trigger='date',
            run_date=run_time,
            args=[customer_phone, agent_id, amount, language, attempt + 1]
        )

def get_audio_url(language_pref: str, audio_type: str = "reminder") -> str:
    lang = (language_pref or "twi").lower()
    if lang not in AUDIO_URLS:
        lang = "twi"
    return AUDIO_URLS[lang].get(audio_type, AUDIO_URLS["twi"]["reminder"])

def make_outbound_call(
    customer_phone: str,
    agent_id: str,
    amount: float,
    alert_id: int = None,
    language_pref: str = None
) -> dict:
    """
    Triggers an outbound voice call via Africa's Talking Voice Gateway.
    """
    db = SessionLocal()
    try:
        if not language_pref:
            user_rec = db.query(User).filter(
                (User.phone_number == customer_phone) | (User.branch != None)
            ).first()
            if user_rec and hasattr(user_rec, "language_pref") and user_rec.language_pref:
                language_pref = user_rec.language_pref
            else:
                language_pref = "twi"

        at_voice_number = os.environ.get("AT_VOICE_PHONE_NUMBER", "+233200000000")
        call_url = "https://voice.sandbox.africastalking.com/call" if AT_USERNAME == "sandbox" else "https://voice.africastalking.com/call"
        client_request_id = f"REQ-VOICE-{uuid.uuid4().hex[:10]}"
        timestamp = datetime.utcnow()

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "apiKey": AT_API_KEY
        }

        payload = {
            "username": AT_USERNAME,
            "from": at_voice_number,
            "to": customer_phone,
            "clientRequestId": client_request_id
        }

        outcome = "queued"
        notes = f"[AT Voice Trigger] Dispatched to {customer_phone} (Lang: {language_pref})"

        try:
            response = requests.post(call_url, data=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201]:
                resp_json = response.json()
                entries = resp_json.get("entries", [])
                if entries:
                    status_text = entries[0].get("status", "Queued")
                    notes = f"[AT Voice Response] Status: {status_text}, RequestId: {client_request_id}"
                    outcome = "queued" if status_text.lower() in ["queued", "success"] else "failed"
            else:
                outcome = "failed"
                notes = f"[AT Voice API Error] HTTP {response.status_code}: {response.text}"
        except Exception as http_err:
            outcome = "failed"
            notes = f"[AT Voice Exception] Network error triggering call: {str(http_err)}"

        call_log = VoiceCallLog(
            customer_phone=customer_phone,
            agent_id=agent_id,
            amount=amount,
            outcome=outcome,
            timestamp=timestamp,
            called_at=timestamp,
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
