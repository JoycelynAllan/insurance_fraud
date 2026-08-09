import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.db import get_db
from backend.app.utils.auth_guard import get_current_user
from backend.app.models.user import User
from backend.app.models.transaction import Transaction
from backend.app.models.voice import VoiceCallLog
from backend.app.services.voice_service import make_outbound_call

logger = logging.getLogger(__name__)
router = APIRouter()

class VoiceTriggerRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID associated with the reminder")
    customer_phone: str = Field(None, description="Customer phone number (optional, defaults to latest in DB)")
    amount: float = Field(None, description="Remittance amount to call about (optional, defaults to latest in DB)")
    language_pref: str = Field("twi", description="Preferred language for call audio: 'twi' or 'dagbani'")
    alert_id: int = Field(None, description="Optional Fraud Alert ID associated with this call")

@router.get("/voice/logs")
def get_voice_logs(
    agent_id: str = Query(None, description="Filter by agent ID"),
    outcome: str = Query(None, description="Filter by outcome (e.g. queued, answered, completed, failed)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns voice campaign call logs from Supabase PostgreSQL.
    """
    try:
        query = db.query(VoiceCallLog)
        
        if agent_id:
            query = query.filter(VoiceCallLog.agent_id == agent_id)
        if outcome:
            query = query.filter(VoiceCallLog.outcome == outcome)
            
        total_count = query.count()
        logs_records = query.order_by(VoiceCallLog.timestamp.desc()).offset(offset).limit(limit).all()
        
        logs = []
        for r in logs_records:
            logs.append({
                "id": r.id,
                "customer_phone": r.customer_phone,
                "agent_id": r.agent_id,
                "amount": float(r.amount),
                "outcome": r.outcome,
                "timestamp": r.timestamp.isoformat() + "Z" if r.timestamp else None,
                "attempt_number": r.attempt_number,
                "notes": r.notes,
                "session_id": r.session_id,
                "language_pref": r.language_pref,
                "dtmf_digits": r.dtmf_digits
            })
            
        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Error querying voice logs from Supabase: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query voice logs from Supabase: {str(e)}"
        )

@router.post("/voice/trigger")
def trigger_voice_call(
    body: VoiceTriggerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    On-demand endpoint to trigger an outbound Africa's Talking voice payment reminder.
    """
    agent_id = body.agent_id
    customer_phone = body.customer_phone
    amount = body.amount
    language_pref = body.language_pref
    alert_id = body.alert_id
    
    # Auto-resolve phone and amount if missing
    if not customer_phone or amount is None:
        latest_tx = db.query(Transaction).filter(
            Transaction.agent_id == agent_id,
            Transaction.customer_phone != None
        ).order_by(Transaction.timestamp.desc()).first()
        
        if not latest_tx:
            raise HTTPException(
                status_code=400,
                detail=f"No transaction details or customer phone found for agent {agent_id} in the database."
            )
            
        if not customer_phone:
            customer_phone = latest_tx.customer_phone
        if amount is None:
            amount = float(latest_tx.amount)
            
    try:
        logger.info(f"Triggering AT Voice Call: agent={agent_id}, phone={customer_phone}, amount={amount}, lang={language_pref}")
        result = make_outbound_call(
            customer_phone=customer_phone,
            agent_id=agent_id,
            amount=amount,
            alert_id=alert_id,
            language_pref=language_pref
        )
        return {
            "status": "success",
            "message": f"Africa's Talking voice call triggered. Outcome: {result.get('outcome', 'queued')}",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error triggering voice call: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Outbound trigger execution failed: {str(e)}"
        )
