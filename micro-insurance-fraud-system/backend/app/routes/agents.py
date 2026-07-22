import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models.transaction import Transaction, TransactionFeature
from backend.app.models.agent import Agent
from backend.app.utils.auth_guard import get_current_user
from backend.app.models.user import User

# Resolve paths dynamically
router_dir = Path(__file__).resolve().parent
ml_dir = router_dir.parent / "ml"

ml_path_str = str(ml_dir)
if ml_path_str not in sys.path:
    sys.path.insert(0, ml_path_str)

from backend.app.ml.fraud_detection import score_transaction

router = APIRouter()

# GET /api/agents/risk
@router.get("/agents/risk")
def get_agents_risk(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns risk scoring details for all agents, sorted descending by risk score.
    Includes aggregated branch, status, amount, and timestamp metrics.
    """
    # Query all transactions and their pre-scored features from the DB
    records = db.query(Transaction, TransactionFeature).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).all()
    
    if not records:
        return []
        
    # Group by agent_id and keep only the most recent transaction for each agent
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
            "risk_score": float(feat.risk_score) if feat.risk_score is not None else 0.0,
            "is_fraud": bool(feat.is_fraud),
            "flag_reason": feat.flag_reason,
            "status": tx.remittance_status,
            "amount": float(tx.amount),
            "date": tx.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results

# GET /api/agents/{agent_id}/trend
@router.get("/agents/{agent_id}/trend")
def get_agent_trend(agent_id: str, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns the last 30 days of transactions for a specific agent from the DB.
    """
    # Cutoff date is 30 days before current time
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    # Query transactions + features from DB for this agent within the last 30 days
    records = db.query(Transaction, TransactionFeature).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).filter(
        Transaction.agent_id == agent_id,
        Transaction.timestamp >= cutoff_date
    ).order_by(Transaction.timestamp.asc()).all()
    
    if not records:
        raise HTTPException(
            status_code=404, 
            detail="Agent not found or no recent transactions"
        )
        
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
