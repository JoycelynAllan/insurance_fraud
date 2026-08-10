import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models.transaction import Transaction, TransactionFeature
from backend.app.models.agent import Agent
from backend.app.utils.auth_guard import get_current_user
from backend.app.models.user import User

router_dir = Path(__file__).resolve().parent
ml_dir = router_dir.parent / "ml"
ml_path_str = str(ml_dir)
if ml_path_str not in sys.path:
    sys.path.insert(0, ml_path_str)

router = APIRouter()

# GET /api/agents and GET /api/agents/risk
@router.get("/agents")
@router.get("/agents/risk")
def get_agents_risk(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns risk scoring details for all monitored agents, sorted descending by risk score.
    Accessible to all authenticated supervisors.
    """
    records = db.query(Transaction, TransactionFeature).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).all()
    
    if not records:
        return []
        
    agent_records = {}
    for tx, feat in records:
        aid = tx.agent_id
        if aid not in agent_records or tx.timestamp > agent_records[aid][0].timestamp:
            agent_records[aid] = (tx, feat)
            
    results = []
    for aid, (tx, feat) in agent_records.items():
        results.append({
            "agent_id": aid,
            "branch": tx.branch,
            "customer_phone": tx.customer_phone,
            "language_pref": getattr(tx, "language_pref", "english") or "english",
            "risk_score": float(feat.risk_score) if feat.risk_score is not None else 0.0,
            "is_fraud": bool(feat.is_fraud),
            "flag_reason": feat.flag_reason,
            "status": tx.remittance_status,
            "amount": float(tx.amount),
            "date": tx.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results

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
        results.append({
            "id": tx.id,
            "agent_id": tx.agent_id,
            "customer_phone": tx.customer_phone,
            "amount": float(tx.amount),
            "payment_method": tx.payment_method,
            "remittance_status": tx.remittance_status,
            "branch": tx.branch,
            "language_pref": getattr(tx, "language_pref", "english") or "english",
            "risk_score": float(feat.risk_score) if feat.risk_score is not None else 0.0,
            "is_fraud": bool(feat.is_fraud),
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
        trend_results.append({
            "timestamp": tx.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
            "amount": float(tx.amount),
            "payment_method": tx.payment_method,
            "remittance_status": tx.remittance_status,
            "risk_score": float(feat.risk_score) if feat.risk_score is not None else 0.0,
            "is_fraud": bool(feat.is_fraud),
            "flag_reason": feat.flag_reason
        })
        
    return trend_results
