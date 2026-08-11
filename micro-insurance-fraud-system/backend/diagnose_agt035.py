import sys
from pathlib import Path

ml_dir = Path(__file__).resolve().parent / "app" / "ml"
if str(ml_dir) not in sys.path:
    sys.path.insert(0, str(ml_dir))

from datetime import datetime, timedelta
from backend.app.db import SessionLocal
from backend.app.models.transaction import Transaction, TransactionFeature
from backend.app.models.alert import FraudAlert
from backend.app.ml.fraud_detection import score_transaction, get_model
from sqlalchemy import func

db = SessionLocal()
try:
    print("--- DIAGNOSING AGT035 DATA AND SCORING ---")

    # 1. Inspect raw rows for AGT035
    records = db.query(Transaction, TransactionFeature).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).filter(Transaction.agent_id == "AGT035").order_by(Transaction.timestamp.desc()).all()

    print(f"Total transaction rows for AGT035: {len(records)}")
    for tx, feat in records[:5]:
        print(f" Tx ID: {tx.id}, Date: {tx.timestamp}, Amount: {tx.amount}, Status: {tx.remittance_status}, DB Feat Score: {feat.risk_score}, Delay: {feat.remittance_delay_hours}, CashRatio: {feat.cash_ratio}")

    # 2. Aggregated features for AGT035 (last 30 days)
    latest_tx = db.query(Transaction).order_by(Transaction.timestamp.desc()).first()
    anchor_date = latest_tx.timestamp if latest_tx else datetime.utcnow()
    cutoff_date = anchor_date - timedelta(days=30)

    agg = db.query(
        Transaction.agent_id,
        func.max(TransactionFeature.remittance_delay_hours).label("remittance_delay_hours"),
        func.avg(TransactionFeature.cash_ratio).label("cash_ratio"),
        func.avg(TransactionFeature.deviation_from_agent_mean).label("deviation_from_agent_mean"),
        func.max(TransactionFeature.missed_consecutive_count).label("missed_consecutive_count"),
        func.avg(Transaction.amount).label("amount")
    ).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).filter(
        Transaction.agent_id == "AGT035",
        Transaction.timestamp >= cutoff_date
    ).group_by(Transaction.agent_id).first()

    if agg:
        feature_dict = {
            "remittance_delay_hours": int(agg.remittance_delay_hours or 0),
            "cash_ratio": float(agg.cash_ratio or 0.0),
            "deviation_from_agent_mean": float(agg.deviation_from_agent_mean or 0.0),
            "missed_consecutive_count": int(agg.missed_consecutive_count or 0),
            "amount": float(agg.amount or 0.0)
        }
        print("\nAggregated feature_dict for AGT035:", feature_dict)
        scored = score_transaction(feature_dict)
        print("Score for AGT035 using aggregated features:", scored)
    else:
        print("No aggregated data found for AGT035 in last 30 days!")

    # 3. Check FraudAlert table for AGT035
    alerts = db.query(FraudAlert).filter(FraudAlert.agent_id == "AGT035").all()
    print(f"\nFraudAlert rows for AGT035: {len(alerts)}")
    for a in alerts:
        print(f" Alert ID: {a.id}, Agent: {a.agent_id}, Score: {a.risk_score}, Status: {a.status}, Reason: {a.flag_reason}")

finally:
    db.close()
