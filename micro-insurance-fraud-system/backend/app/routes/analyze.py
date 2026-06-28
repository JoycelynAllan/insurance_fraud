import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from fastapi import APIRouter, Request, HTTPException
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
def analyze_transaction(request: Request, body: AnalyzeRequest):
    df = request.app.state.features_df
    
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

    # 2. Look up agent's cash_ratio and mean amount from features CSV
    agent_rows = df[df['agent_id'] == body.agent_id]
    
    if not agent_rows.empty:
        cash_ratio = float(agent_rows.iloc[0]['cash_ratio'])
        agent_mean_amount = float(agent_rows['amount'].mean())
        agent_rows_sorted = agent_rows.sort_values(by='timestamp')
        last_missed_consecutive = int(agent_rows_sorted.iloc[-1]['missed_consecutive_count'])
    else:
        # Default fallback values if the agent is new/not found
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

# GET /api/agents/risk
@router.get("/agents/risk")
def get_agents_risk(request: Request):
    df = request.app.state.features_df
    
    # Ensure timestamp column is parsed as datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    results = []
    grouped = df.groupby('agent_id')
    
    for agent_id, group in grouped:
        # Aggregate features for each agent:
        # - Most recent remittance_delay_hours
        most_recent_row = group.sort_values(by='timestamp').iloc[-1]
        rem_delay = int(most_recent_row['remittance_delay_hours'])
        
        # - Cash ratio (value from any of the agent's rows as it's constant)
        cash_ratio = float(group.iloc[0]['cash_ratio'])
        
        # - Max missed_consecutive_count
        missed_count = int(group['missed_consecutive_count'].max())
        
        # - Mean deviation_from_agent_mean
        mean_dev = float(group['deviation_from_agent_mean'].mean())
        
        # - Mean amount
        mean_amt = float(group['amount'].mean())
        
        feature_dict = {
            'remittance_delay_hours': rem_delay,
            'cash_ratio': cash_ratio,
            'deviation_from_agent_mean': mean_dev,
            'missed_consecutive_count': missed_count,
            'amount': mean_amt
        }
        
        # Score the aggregated profile of the agent
        scored = score_transaction(feature_dict)
        
        results.append({
            "agent_id": agent_id,
            "risk_score": scored["risk_score"],
            "is_fraud": scored["is_fraud"],
            "flag_reason": scored["flag_reason"]
        })
        
    # Sort results descending by risk_score
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results

# GET /api/agents/{agent_id}/trend
@router.get("/agents/{agent_id}/trend")
def get_agent_trend(agent_id: str, request: Request):
    df = request.app.state.features_df
    
    # Ensure timestamp column is parsed as datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    # Verify if the agent exists
    agent_exists = (df['agent_id'] == agent_id).any()
    if not agent_exists:
        raise HTTPException(
            status_code=404, 
            detail="Agent not found or no recent transactions"
        )
        
    # Filter transactions to those from the last 30 days from UTC now
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    agent_df = df[(df['agent_id'] == agent_id) & (df['timestamp'] >= cutoff_date)]
    
    if agent_df.empty:
        raise HTTPException(
            status_code=404, 
            detail="Agent not found or no recent transactions"
        )
        
    # Sort chronologically (timestamp ascending)
    agent_df_sorted = agent_df.sort_values(by='timestamp')
    
    trend_results = []
    for _, row in agent_df_sorted.iterrows():
        feature_dict = {
            'remittance_delay_hours': int(row['remittance_delay_hours']),
            'cash_ratio': float(row['cash_ratio']),
            'deviation_from_agent_mean': float(row['deviation_from_agent_mean']),
            'missed_consecutive_count': int(row['missed_consecutive_count']),
            'amount': float(row['amount'])
        }
        
        scored = score_transaction(feature_dict)
        ts_str = row['timestamp'].strftime('%Y-%m-%dT%H:%M:%S')
        
        trend_results.append({
            "timestamp": ts_str,
            "amount": float(row['amount']),
            "payment_method": str(row['payment_method']),
            "remittance_status": str(row['remittance_status']),
            "risk_score": scored["risk_score"],
            "is_fraud": scored["is_fraud"],
            "flag_reason": scored["flag_reason"]
        })
        
    return trend_results
