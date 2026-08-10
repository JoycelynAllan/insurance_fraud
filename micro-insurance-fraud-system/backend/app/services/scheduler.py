import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from backend.app.db import SessionLocal
from backend.app.models.transaction import Transaction, TransactionFeature
from backend.app.models.alert import FraudAlert
from backend.app.models.user import User
from backend.app.ml.fraud_detection import score_transaction
from backend.app.routes.alerts import broadcast_alert
from backend.app.services.voice_service import make_outbound_call, schedule_retry

logger = logging.getLogger(__name__)

# Initialize the AsyncIOScheduler
scheduler = AsyncIOScheduler()

async def run_fraud_check_job():
    """
    Background job that runs every 5 minutes.
    Loads recent transactions from the database, scores them,
    persists + broadcasts PENDING alerts for risk_score >= 70%,
    and schedules multilingual voice/SMS reminders for missed payments.
    """
    db = SessionLocal()
    called_phones = set()
    try:
        logger.info("Executing scheduled database-backed fraud checking job...")
        
        # Query 10 most recent transactions joined with their features
        records = db.query(Transaction, TransactionFeature).join(
            TransactionFeature, Transaction.id == TransactionFeature.transaction_id
        ).order_by(Transaction.timestamp.desc()).limit(10).all()
        
        if not records:
            logger.info("No transactions found in database to evaluate.")
            return
            
        for tx, feat in records:
            feature_dict = {
                'remittance_delay_hours': int(feat.remittance_delay_hours),
                'cash_ratio': float(feat.cash_ratio) if feat.cash_ratio is not None else 0.0,
                'deviation_from_agent_mean': float(feat.deviation_from_agent_mean) if feat.deviation_from_agent_mean is not None else 0.0,
                'missed_consecutive_count': int(feat.missed_consecutive_count),
                'amount': float(tx.amount)
            }
            
            # Score transaction using the two-stage model pipeline
            scored = score_transaction(feature_dict)
            risk_score = float(scored['risk_score'])
            score_pct = risk_score * 100.0 if risk_score <= 1.0 else risk_score

            # Look up customer call language preference directly from transaction row
            customer_lang = getattr(tx, "language_pref", "english") or "english"

            # Trigger automated retry schedule if remittance_status == "missed"
            if tx.remittance_status == "missed" and tx.customer_phone:
                if tx.customer_phone not in called_phones:
                    called_phones.add(tx.customer_phone)
                    try:
                        logger.info(f"Triggering automated reminder retry schedule for customer {tx.customer_phone} (Lang: {customer_lang})")
                        schedule_retry(
                            customer_phone=tx.customer_phone,
                            agent_id=tx.agent_id,
                            amount=float(tx.amount),
                            language=customer_lang,
                            attempt=1
                        )
                    except Exception as ve:
                        logger.error(f"Voice reminder schedule retry failed: {str(ve)}")

            # Broadcast and persist if risk score >= 70 (or 0.70)
            if score_pct >= 70.0:
                # Check if a PENDING alert already exists for this agent
                pending_alert = db.query(FraudAlert).filter(
                    FraudAlert.agent_id == tx.agent_id,
                    FraudAlert.status == "PENDING"
                ).first()
                
                if not pending_alert:
                    now_dt = datetime.utcnow()
                    flag_reason_str = str(scored.get("flag_reason", f"Risk score {score_pct:.1f}% flagged by ML model"))
                    logger.info(f"High risk transaction detected! Saving PENDING alert to DB: Tx ID {tx.id}, Agent {tx.agent_id}, Score {score_pct:.1f}%")
                    
                    # Persist alert to database
                    alert_obj = FraudAlert(
                        agent_id=tx.agent_id,
                        transaction_id=tx.id,
                        risk_score=score_pct,
                        flag_reason=flag_reason_str,
                        branch=tx.branch,
                        status="PENDING",
                        alerted_at=now_dt,
                        acknowledged=False
                    )
                    db.add(alert_obj)
                    db.commit()
                    db.refresh(alert_obj)
                    
                    # Broadcast via WebSocket
                    alert_payload = {
                        "id": str(alert_obj.id),
                        "agent_id": str(tx.agent_id),
                        "risk_score": score_pct,
                        "flag_reason": flag_reason_str,
                        "status": "PENDING",
                        "created_at": now_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                    await broadcast_alert(alert_payload)
                else:
                    logger.info(f"PENDING alert for Agent {tx.agent_id} already exists in DB. Suppressing duplicate creation.")
                    
    except Exception as e:
        logger.error(f"Exception raised in run_fraud_check_job: {str(e)}")
    finally:
        db.close()

# Add the job to fire every 5 minutes
scheduler.add_job(run_fraud_check_job, 'interval', minutes=5)
