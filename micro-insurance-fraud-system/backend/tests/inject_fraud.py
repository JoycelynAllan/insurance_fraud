import sys
import os
import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

# Add project root and ml directory to sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "app" / "ml"))

# Load env vars
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from backend.app.db import SessionLocal
from backend.app.models.agent import Agent
from backend.app.models.transaction import Transaction, TransactionFeature
from backend.app.models.alert import FraudAlert
from backend.app.services.scheduler import run_fraud_check_job

async def run_injection_test():
    print("Connecting to database...")
    db = SessionLocal()
    
    # Resolve a valid agent_id from the agents table
    agent = db.query(Agent).first()
    if not agent:
        print("ERROR: No agents found in the database. Cannot run injection test.")
        db.close()
        return

    print(f"Using agent: {agent.agent_id} (Branch: {agent.branch})")

    # Define test parameters
    customer_phone = "+233201234567"
    tx_id = None
    alert_id = None

    try:
        # 1. Insert one synthetic row directly into the transactions and transaction_features Supabase tables
        print("Injecting synthetic high-risk transaction...")
        tx = Transaction(
            agent_id=agent.agent_id,
            customer_id="CUST999",
            customer_phone=customer_phone,
            amount=500.00,
            timestamp=datetime.utcnow(),
            payment_method="momo",
            remittance_status="missed",
            branch=agent.branch
        )
        db.add(tx)
        db.commit()
        tx_id = tx.id
        print(f"Transaction injected with ID: {tx_id}")

        feat = TransactionFeature(
            transaction_id=tx_id,
            remittance_delay_hours=300,
            cash_ratio=0.85,
            deviation_from_agent_mean=200.0,
            missed_consecutive_count=4,
            is_fraud=True,
            risk_score=88.0,
            flag_reason="Injected test high-risk transaction"
        )
        db.add(feat)
        db.commit()
        print("Transaction features injected successfully.")

        # 2. Call the scheduler job function directly
        print("Triggering scheduled database-backed fraud checking job...")
        await run_fraud_check_job()

        # 3. Confirms a fraud_alerts row was inserted in Supabase
        alert = db.query(FraudAlert).filter(FraudAlert.transaction_id == tx_id).first()
        if alert:
            alert_id = alert.id
            print(f"[SUCCESS] Fraud Alert found in Supabase! Alert ID: {alert_id}, Risk Score: {alert.risk_score}")
        else:
            print("[ERROR] No Fraud Alert found in Supabase for the injected transaction!")

        # 4. Confirms a call_logs.db row was written
        db_path = Path(__file__).resolve().parents[2] / "micro-insurance-fraud-system" / "voice" / "call_logs.db"
        if not db_path.exists():
            db_path = Path(__file__).resolve().parents[2] / "voice" / "call_logs.db"
            
        print(f"Checking call logs database at {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM call_logs WHERE customer_phone = ? ORDER BY id DESC LIMIT 1", (customer_phone,))
        row = cursor.fetchone()
        if row:
            print(f"[SUCCESS] Call log recorded in SQLite! Log details: {row}")
        else:
            print(f"[ERROR] No call log found in SQLite for phone {customer_phone}!")
        conn.close()

    except Exception as e:
        print(f"Exception during test: {str(e)}")
    finally:
        # 5. Clean up after: delete the injected test row from all tables when done
        print("Cleaning up injected database rows...")
        if alert_id:
            db.query(FraudAlert).filter(FraudAlert.id == alert_id).delete()
        if tx_id:
            # Delete features and transaction (features will cascade, but delete explicitly to be safe)
            db.query(TransactionFeature).filter(TransactionFeature.transaction_id == tx_id).delete()
            db.query(Transaction).filter(Transaction.id == tx_id).delete()
        db.commit()
        db.close()
        print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(run_injection_test())
