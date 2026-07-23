import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from backend.app.db import SessionLocal
from backend.app.models.transaction import Transaction, TransactionFeature
from backend.app.models.alert import FraudAlert
from backend.app.ml.fraud_detection import score_transaction
from backend.app.routes.alerts import broadcast_alert
from voice.dograh_trigger import trigger_payment_reminder_call

logger = logging.getLogger(__name__)

# Initialize the AsyncIOScheduler
scheduler = AsyncIOScheduler()

async def run_fraud_check_job():
    """
    Background job that runs every 5 minutes.
    Loads the 10 most recent transactions from the database,
    scores them, and persists + broadcasts an alert for any transaction with risk_score >= 70.
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
            
            # Outbound reminder trigger
            if bool(scored.get("is_fraud")) and tx.remittance_status == "missed":
                if tx.customer_phone and tx.customer_phone not in called_phones:
                    called_phones.add(tx.customer_phone)
                    try:
                        logger.info(f"Triggering outbound voice reminder for customer {tx.customer_phone}")
                        trigger_payment_reminder_call(
                            customer_phone=tx.customer_phone,
                            agent_id=tx.agent_id,
                            amount=float(tx.amount)
                        )
                    except Exception as ve:
                        logger.error(f"Voice reminder call trigger failed: {str(ve)}")

            # Broadcast and persist if risk score >= 70
            if risk_score >= 70:
                # Check for duplicate alerts for this transaction within the last hour
                one_hour_ago = datetime.utcnow() - timedelta(hours=1)
                duplicate = db.query(FraudAlert).filter(
                    FraudAlert.transaction_id == tx.id,
                    FraudAlert.alerted_at >= one_hour_ago
                ).first()
                
                if not duplicate:
                    logger.info(f"High risk transaction detected! Saving alert to DB: Tx ID {tx.id}, Agent {tx.agent_id}")
                    # Persist alert to database
                    alert_obj = FraudAlert(
                        agent_id=tx.agent_id,
                        transaction_id=tx.id,
                        risk_score=risk_score,
                        flag_reason=str(scored['flag_reason']),
                        branch=tx.branch,
                        alerted_at=datetime.utcnow(),
                        acknowledged=False
                    )
                    db.add(alert_obj)
                    db.commit()
                    
                    # Broadcast via WebSocket
                    alert_payload = {
                        "agent_id": str(tx.agent_id),
                        "risk_score": risk_score,
                        "is_fraud": bool(scored['is_fraud']),
                        "flag_reason": str(scored['flag_reason']),
                        "timestamp": tx.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                    await broadcast_alert(alert_payload)
                else:
                    logger.info(f"Duplicate alert for Transaction {tx.id} within the same hour was suppressed.")
                    
    except Exception as e:
        logger.error(f"Exception raised in run_fraud_check_job: {str(e)}")
    finally:
        db.close()

# Add the job to fire every 5 minutes
scheduler.add_job(run_fraud_check_job, 'interval', minutes=5)
