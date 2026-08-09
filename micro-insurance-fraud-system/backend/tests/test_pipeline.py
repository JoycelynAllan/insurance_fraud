import sys
import os
import sqlite3
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
from backend.app.models.transaction import Transaction, TransactionFeature
from backend.app.ml.fraud_detection import score_transaction
from backend.app.services.voice_service import make_outbound_call

def run_test():
    print("Connecting to database...")
    db = SessionLocal()
    try:
        # 1. Pick a known fraudulent row from transaction_features in Supabase (is_fraud=true, remittance_status='missed')
        record = db.query(Transaction, TransactionFeature).join(
            TransactionFeature, Transaction.id == TransactionFeature.transaction_id
        ).filter(
            TransactionFeature.is_fraud == True,
            Transaction.remittance_status == "missed"
        ).first()

        if not record:
            print("WARNING: No fraudulent missed rows found in database! Falling back to creating a mock transaction.")
            # If none exists, we will define mock features for the test
            customer_phone = "+233201234567"
            agent_id = "AGT001"
            amount = 150.0
            feature_dict = {
                'remittance_delay_hours': 350,
                'cash_ratio': 0.9,
                'deviation_from_agent_mean': 150.0,
                'missed_consecutive_count': 5,
                'amount': amount
            }
        else:
            tx, feat = record
            print(f"Picked transaction ID: {tx.id}, Phone: {tx.customer_phone}, Amount: {tx.amount}")
            customer_phone = tx.customer_phone or "+233201234567"
            agent_id = tx.agent_id
            amount = float(tx.amount)
            feature_dict = {
                'remittance_delay_hours': int(feat.remittance_delay_hours),
                'cash_ratio': float(feat.cash_ratio) if feat.cash_ratio is not None else 0.0,
                'deviation_from_agent_mean': float(feat.deviation_from_agent_mean) if feat.deviation_from_agent_mean is not None else 0.0,
                'missed_consecutive_count': int(feat.missed_consecutive_count),
                'amount': amount
            }

        # 2. Call score_transaction() directly with its features
        print(f"Scoring features: {feature_dict}")
        scored = score_transaction(feature_dict)
        risk_score = float(scored['risk_score'])
        is_fraud = bool(scored['is_fraud'])
        print(f"Scoring result: risk_score={risk_score}, is_fraud={is_fraud}")

        # 3. Assert risk_score >= 70 and is_fraud == True
        assert risk_score >= 70, f"Expected risk_score >= 70, got {risk_score}"
        assert is_fraud == True, "Expected is_fraud == True"
        print("[OK] Assertions passed: transaction is classified as fraudulent.")

        # 4. Call make_outbound_call()
        print(f"Triggering payment reminder call to {customer_phone} (Agent {agent_id}, Amount GHS {amount})")
        outcome_dict = make_outbound_call(
            customer_phone=customer_phone,
            agent_id=agent_id,
            amount=amount
        )

        # 5. Print the call outcome
        print(f"Call trigger result: {outcome_dict}")

        # 6. Query Supabase PostgreSQL VoiceCallLog to confirm log was written
        from backend.app.models.voice import VoiceCallLog
        last_log = db.query(VoiceCallLog).order_by(VoiceCallLog.timestamp.desc()).first()
        print("--- LAST VOICE CALL LOG IN SUPABASE ---")
        if last_log:
            print(f"ID: {last_log.id}, Phone: {last_log.customer_phone}, Agent: {last_log.agent_id}, Outcome: {last_log.outcome}, Notes: {last_log.notes}")

    finally:
        db.close()

if __name__ == "__main__":
    run_test()
