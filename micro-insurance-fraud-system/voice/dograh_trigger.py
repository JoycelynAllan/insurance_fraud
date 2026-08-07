import os
import sqlite3
import re
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dograh_sdk import DograhClient
from dograh_sdk._generated_models import InitiateCallRequest
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

# Initialize background scheduler for retries
retry_scheduler = BackgroundScheduler()
# Check if scheduler is already running to avoid double start warnings
if not retry_scheduler.running:
    retry_scheduler.start()

def init_db():
    db_path = Path(__file__).resolve().parent / "call_logs.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS call_logs (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      customer_phone  TEXT NOT NULL,
      agent_id        TEXT NOT NULL,
      amount          REAL NOT NULL,
      outcome         TEXT NOT NULL,
      timestamp       TEXT NOT NULL,
      attempt_number  INTEGER DEFAULT 1,
      notes           TEXT
    );
    """)
    conn.commit()
    conn.close()

init_db()

def _log_attempt(customer_phone: str, agent_id: str, amount: float, outcome: str, timestamp: str, attempt_number: int, notes: str = None):
    db_path = Path(__file__).resolve().parent / "call_logs.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO call_logs (customer_phone, agent_id, amount, outcome, timestamp, attempt_number, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (customer_phone, agent_id, amount, outcome, timestamp, attempt_number, notes))
    conn.commit()
    conn.close()

def trigger_payment_reminder_call(
    customer_phone: str,
    agent_id: str,
    amount: float,
    attempt_number: int = 1
) -> dict:
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Load settings from environment
    api_url = os.environ.get("DOGRAH_API_URL", "http://localhost:8000")
    api_token = os.environ.get("DOGRAH_API_TOKEN", "mock_token")
    workflow_id_str = os.environ.get("DOGRAH_WORKFLOW_ID", "1")
    
    if api_token == "mock_token" or "localhost" in api_url:
        logger.warning(
            f"[DOGRAH DIAGNOSTIC] Using fallback credentials (api_url={api_url}, api_token={api_token}). "
            "If deployed on Render, set DOGRAH_API_URL and DOGRAH_API_TOKEN in Render environment variables."
        )

    try:
        workflow_id = int(workflow_id_str)
    except ValueError:
        workflow_id = 1

    outcome = "failed"
    notes = None

    try:
        # Load dotenv to read .env if present
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        with DograhClient(base_url=api_url, api_key=api_token) as client:
            # Place outbound call via Dograh Client
            resp = client.test_phone_call(
                body=InitiateCallRequest(
                    workflow_id=workflow_id,
                    phone_number=customer_phone
                )
            )
            
            # Extract run name from JSON response or string representation
            message = ""
            if isinstance(resp, dict):
                message = resp.get("message", "")
            elif hasattr(resp, "message"):
                message = resp.message
            else:
                message = str(resp)

            match = re.search(r"run name\s+(WR-TEL-OUT-\d+)", message)
            run_name = match.group(1) if match else None
            
            if run_name:
                # Poll list of runs to find the numeric run_id for this run_name
                run_id = None
                for _ in range(10):  # poll up to 10 seconds
                    list_resp = client._http.get(f"/workflow/{workflow_id}/runs")
                    if list_resp.status_code == 200:
                        runs_data = list_resp.json()
                        for r in runs_data.get("runs", []):
                            if r.get("name") == run_name:
                                run_id = r.get("id")
                                break
                    if run_id:
                        break
                    time.sleep(1)

                if run_id:
                    # Poll details for run completion and callback logging status
                    for _ in range(30):  # poll up to 30 seconds
                        detail_resp = client._http.get(f"/workflow/{workflow_id}/runs/{run_id}")
                        if detail_resp.status_code == 200:
                            run_detail = detail_resp.json()
                            if run_detail.get("is_completed"):
                                logs = run_detail.get("logs", {})
                                callbacks = logs.get("telephony_status_callbacks", [])
                                if callbacks:
                                    last_status = callbacks[-1].get("status", "").lower()
                                    if last_status in ["completed", "answered"]:
                                        outcome = "answered"
                                    elif last_status in ["busy", "no-answer", "timeout", "no_answer"]:
                                        outcome = "no_answer"
                                    else:
                                        outcome = "failed"
                                else:
                                    outcome = "answered"  # fallback if no callbacks (completed state implies success)
                                notes = f"Completed run ID {run_id}"
                                break
                        time.sleep(1)
                else:
                    notes = f"Could not resolve run ID for name: {run_name}"
            else:
                notes = f"Initiate response did not match run name. Msg: {message}"
    except Exception as e:
        logger.error(f"Error connecting to Dograh outbound endpoint: {str(e)}")
        outcome = "failed"
        notes = f"Dograh connection error: {str(e)}"

    # Log attempt details to SQLite3 call_logs
    _log_attempt(customer_phone, agent_id, amount, outcome, timestamp, attempt_number, notes)
    
    # If the call wasn't answered and we haven't reached the 3-attempt limit, trigger the retry scheduler
    if outcome == "no_answer" and attempt_number < 3:
        schedule_retry(customer_phone, agent_id, amount, attempts=attempt_number + 1)
        
    return {
        "outcome": outcome,
        "notes": notes,
        "timestamp": timestamp,
        "customer_phone": customer_phone,
        "agent_id": agent_id
    }

def schedule_retry(
    customer_phone: str,
    agent_id: str,
    amount: float,
    attempts: int = 1
) -> None:
    if attempts == 1:
        trigger_payment_reminder_call(customer_phone, agent_id, amount, attempt_number=1)
    elif attempts <= 3:
        # Schedule next attempt in 2 hours
        retry_scheduler.add_job(
            trigger_payment_reminder_call,
            'date',
            run_date=datetime.now() + timedelta(hours=2),
            args=[customer_phone, agent_id, amount, attempts]
        )
