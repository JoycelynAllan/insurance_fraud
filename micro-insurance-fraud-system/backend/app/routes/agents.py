import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db import get_db
from backend.app.models.transaction import Transaction, TransactionFeature
from backend.app.models.agent import Agent
from backend.app.utils.auth_guard import get_current_user
from backend.app.models.user import User
from backend.app.ml.fraud_detection import score_transaction

router_dir = Path(__file__).resolve().parent
ml_dir = router_dir.parent / "ml"
ml_path_str = str(ml_dir)
if ml_path_str not in sys.path:
    sys.path.insert(0, ml_path_str)

router = APIRouter()

def compute_all_agent_risk_scores(db: Session):
    """
    Computes aggregated per-agent risk scores over recent transactions (30-day window).
    Uses aggregated per-agent features:
      - MAX(remittance_delay_hours)
      - AVG(cash_ratio)
      - AVG(deviation_from_agent_mean)
      - MAX(missed_consecutive_count)
      - AVG(amount)
    Scores each agent using score_transaction.
    Returns list of dicts sorted descending by risk_score.
    """
    latest_tx = db.query(Transaction).order_by(Transaction.timestamp.desc()).first()
    anchor_date = latest_tx.timestamp if latest_tx else datetime.utcnow()
    cutoff_date = anchor_date - timedelta(days=30)

    # Aggregated query per agent over last 30 days
    aggregated_records = db.query(
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

    # Fallback to all transactions if no 30-day cutoff records found
    if not aggregated_records:
        aggregated_records = db.query(
            Transaction.agent_id,
            func.max(TransactionFeature.remittance_delay_hours).label("remittance_delay_hours"),
            func.avg(TransactionFeature.cash_ratio).label("cash_ratio"),
            func.avg(TransactionFeature.deviation_from_agent_mean).label("deviation_from_agent_mean"),
            func.max(TransactionFeature.missed_consecutive_count).label("missed_consecutive_count"),
            func.avg(Transaction.amount).label("amount")
        ).join(
            TransactionFeature, Transaction.id == TransactionFeature.transaction_id
        ).group_by(Transaction.agent_id).all()

    # Get latest transaction per agent for display metadata (branch, customer_phone, remittance_status, language_pref)
    latest_per_agent = {}
    all_txs = db.query(Transaction).order_by(Transaction.timestamp.desc()).all()
    for tx in all_txs:
        if tx.agent_id not in latest_per_agent:
            latest_per_agent[tx.agent_id] = tx

    results = []
    for row in aggregated_records:
        aid = row.agent_id
        tx = latest_per_agent.get(aid)

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

        results.append({
            "agent_id": aid,
            "branch": tx.branch if tx else "Accra",
            "customer_phone": tx.customer_phone if tx else None,
            "language_pref": getattr(tx, "language_pref", "english") or "english" if tx else "english",
            "risk_score": risk_score,
            "is_fraud": is_fraud,
            "flag_reason": scored["flag_reason"],
            "status": tx.remittance_status if tx else "pending",
            "amount": float(tx.amount) if tx else float(row.amount or 0.0),
            "date": tx.timestamp.strftime('%Y-%m-%d %H:%M:%S') if tx else "",
            "latest_tx_id": tx.id if tx else None
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results

# GET /api/agents and GET /api/agents/risk
@router.get("/agents")
@router.get("/agents/risk")
def get_agents_risk(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns risk scoring details for all monitored agents using aggregated feature scoring, sorted descending by risk score.
    Accessible to all authenticated supervisors.
    """
    return compute_all_agent_risk_scores(db)

# GET /api/agents/{agent_id}/transactions
@router.get("/agents/{agent_id}/transactions")
def get_agent_transactions(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all transactions for a specific agent.
    Accessible to authenticated supervisors.
    """
    records = db.query(Transaction, TransactionFeature).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).filter(
        Transaction.agent_id == agent_id
    ).order_by(Transaction.timestamp.desc()).all()
    
    results = []
    for tx, feat in records:
        sc = float(feat.risk_score) if feat.risk_score is not None else 0.0
        results.append({
            "id": tx.id,
            "agent_id": tx.agent_id,
            "customer_phone": tx.customer_phone,
            "amount": float(tx.amount),
            "payment_method": tx.payment_method,
            "remittance_status": tx.remittance_status,
            "branch": tx.branch,
            "language_pref": getattr(tx, "language_pref", "english") or "english",
            "risk_score": sc,
            "is_fraud": bool(sc >= 70.0),
            "flag_reason": feat.flag_reason,
            "timestamp": tx.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "date": tx.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    return results

# GET /api/agents/{agent_id}/trend
@router.get("/agents/{agent_id}/trend")
def get_agent_trend(agent_id: str, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns transaction history trend for a specific agent.
    """
    latest_tx = db.query(Transaction).order_by(Transaction.timestamp.desc()).first()
    anchor_date = latest_tx.timestamp if latest_tx else datetime.utcnow()
    cutoff_date = anchor_date - timedelta(days=30)
    
    records = db.query(Transaction, TransactionFeature).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).filter(
        Transaction.agent_id == agent_id,
        Transaction.timestamp >= cutoff_date
    ).order_by(Transaction.timestamp.asc()).all()
    
    trend_results = []
    for tx, feat in records:
        sc = float(feat.risk_score) if feat.risk_score is not None else 0.0
        trend_results.append({
            "timestamp": tx.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
            "amount": float(tx.amount),
            "payment_method": tx.payment_method,
            "remittance_status": tx.remittance_status,
            "risk_score": sc,
            "is_fraud": bool(sc >= 70.0),
            "flag_reason": feat.flag_reason
        })
        
    return trend_results
