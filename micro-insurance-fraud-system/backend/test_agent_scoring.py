import sys
from pathlib import Path

ml_dir = Path(__file__).resolve().parent / "app" / "ml"
if str(ml_dir) not in sys.path:
    sys.path.insert(0, str(ml_dir))

from datetime import datetime, timedelta
from sqlalchemy import func
from backend.app.db import SessionLocal
from backend.app.models.transaction import Transaction, TransactionFeature
from backend.app.ml.fraud_detection import score_transaction

db = SessionLocal()
try:
    print("--- COMPUTING UNIFIED AGGREGATED RISK SCORES FOR ALL AGENTS ---")

    latest_tx = db.query(Transaction).order_by(Transaction.timestamp.desc()).first()
    anchor_date = latest_tx.timestamp if latest_tx else datetime.utcnow()
    cutoff_date = anchor_date - timedelta(days=30)

    # Query aggregated features per agent over last 30 days
    results = db.query(
        Transaction.agent_id,
        func.max(TransactionFeature.remittance_delay_hours).label("remittance_delay_hours"),
        func.avg(TransactionFeature.cash_ratio).label("cash_ratio"),
        func.avg(TransactionFeature.deviation_from_agent_mean).label("deviation_from_agent_mean"),
        func.max(TransactionFeature.missed_consecutive_count).label("missed_consecutive_count"),
        func.avg(Transaction.amount).label("amount")
    ).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).filter(
        Transaction.timestamp >= cutoff_date
    ).group_by(Transaction.agent_id).all()

    # Also map latest transaction details per agent (branch, customer_phone, remittance_status, language_pref)
    latest_per_agent = {}
    all_txs = db.query(Transaction).order_by(Transaction.timestamp.desc()).all()
    for tx in all_txs:
        if tx.agent_id not in latest_per_agent:
            latest_per_agent[tx.agent_id] = tx

    scored_agents = []
    for row in results:
        aid = row.agent_id
        latest_tx = latest_per_agent.get(aid)
        
        feature_dict = {
            "remittance_delay_hours": int(row.remittance_delay_hours or 0),
            "cash_ratio": float(row.cash_ratio or 0.0),
            "deviation_from_agent_mean": float(row.deviation_from_agent_mean or 0.0),
            "missed_consecutive_count": int(row.missed_consecutive_count or 0),
            "amount": float(row.amount or 0.0)
        }
        
        scored = score_transaction(feature_dict)
        risk_score = float(scored["risk_score"])
        is_fraud = bool(risk_score >= 70.0)
        
        scored_agents.append({
            "agent_id": aid,
            "branch": latest_tx.branch if latest_tx else "Accra",
            "customer_phone": latest_tx.customer_phone if latest_tx else None,
            "language_pref": getattr(latest_tx, "language_pref", "english") or "english",
            "risk_score": risk_score,
            "is_fraud": is_fraud,
            "flag_reason": scored["flag_reason"],
            "status": latest_tx.remittance_status if latest_tx else "pending",
            "amount": float(latest_tx.amount) if latest_tx else float(row.amount or 0.0),
            "date": latest_tx.timestamp.strftime('%Y-%m-%d %H:%M:%S') if latest_tx else ""
        })

    scored_agents.sort(key=lambda x: x["risk_score"], reverse=True)

    print(f"Total agents aggregated & scored: {len(scored_agents)}")
    print("\nTop 10 highest risk agents:")
    for a in scored_agents[:10]:
        print(f" Agent {a['agent_id']:<8}: Risk Score = {a['risk_score']:>6.2f}%, is_fraud = {a['is_fraud']}, Status = {a['status']}")

    print("\nLow-risk agents sample (including AGT035 if present):")
    for a in scored_agents:
        if a['agent_id'] == 'AGT035' or a['risk_score'] < 40.0:
            print(f" Agent {a['agent_id']:<8}: Risk Score = {a['risk_score']:>6.2f}%, is_fraud = {a['is_fraud']}, Status = {a['status']}")

finally:
    db.close()
