import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models.transaction import Transaction, TransactionFeature
from backend.app.utils.auth_guard import get_current_user
from backend.app.models.user import User
from pydantic import BaseModel, Field

# Resolve paths dynamically
router_dir = Path(__file__).resolve().parent
ml_dir = router_dir.parent / "ml"

# Programmatically add the 'ml' directory to sys.path to allow joblib/pickle
# to correctly resolve the pickled 'data_preprocessing' module namespace.
ml_path_str = str(ml_dir)
if ml_path_str not in sys.path:
    sys.path.insert(0, ml_path_str)

# Safely import core models and score function
from backend.app.ml.fraud_detection import score_transaction

router = APIRouter()

# Pydantic models for input validation
class AnalyzeRequest(BaseModel):
    agent_id: str = Field(..., description="Unique agent identifier, e.g. AGT001")
    customer_id: str = Field(..., description="Unique customer identifier, e.g. CUST0042")
    amount: float = Field(..., description="Transaction amount in GHS")
    payment_method: str = Field(..., description="Payment method: cash, momo, or bank_transfer")
    remittance_status: str = Field(..., description="Remittance status: remitted, pending, or missed")
    branch: str = Field(..., description="Branch location, e.g. Kumasi")

# POST /api/analyze
@router.post("/analyze")
def analyze_transaction(
    request: Request,
    body: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Query transaction and feature records for this agent from the DB
    records = db.query(Transaction, TransactionFeature).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).filter(Transaction.agent_id == body.agent_id).all()
    
    # 1. Compute remittance_delay_hours from status
    status_lower = body.remittance_status.lower()
    if status_lower == "remitted":
        remittance_delay_hours = 0
    elif status_lower == "pending":
        remittance_delay_hours = 72  # fallback default delay for pending status
    elif status_lower == "missed":
        remittance_delay_hours = 312 # aligns with the expected delay hours for missed status
    else:
        remittance_delay_hours = 0

    # 2. Look up agent's cash_ratio and mean amount from DB
    if records:
        # Get cash ratio from the first/current configuration
        cash_ratio = float(records[0][1].cash_ratio) if records[0][1].cash_ratio is not None else 0.0
        
        # Calculate agent mean amount from transaction history
        amounts = [float(r[0].amount) for r in records]
        agent_mean_amount = sum(amounts) / len(amounts)
        
        # Get missed consecutive count from the most recent transaction
        sorted_records = sorted(records, key=lambda x: x[0].timestamp)
        last_missed_consecutive = int(sorted_records[-1][1].missed_consecutive_count)
    else:
        # Default fallback values if the agent is new/not found in the DB
        cash_ratio = 0.0
        agent_mean_amount = body.amount
        last_missed_consecutive = 0
        
    deviation_from_agent_mean = body.amount - agent_mean_amount
    
    # Compute missed_consecutive_count for the current transaction
    if status_lower == "missed":
        missed_consecutive_count = last_missed_consecutive + 1
    else:
        missed_consecutive_count = 0
        
    # Assemble feature dictionary
    feature_dict = {
        'remittance_delay_hours': remittance_delay_hours,
        'cash_ratio': cash_ratio,
        'deviation_from_agent_mean': deviation_from_agent_mean,
        'missed_consecutive_count': missed_consecutive_count,
        'amount': body.amount
    }
    
    # Score the transaction using the machine learning models
    result = score_transaction(feature_dict)
    return result
