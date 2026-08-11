import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from backend.app.db import SessionLocal
from backend.app.models.transaction import Transaction
from backend.app.models.alert import FraudAlert
from backend.app.routes.alerts import broadcast_alert
from backend.app.routes.agents import compute_all_agent_risk_scores
from backend.app.services.voice_service import schedule_retry

logger = logging.getLogger(__name__)

# Initialize the AsyncIOScheduler
scheduler = AsyncIOScheduler()

async def run_fraud_check_job():
    """
    Background job that runs every 5 minutes.
    Computes aggregated per-agent risk scores using score_transaction,
    persists + broadcasts PENDING alerts ONLY for risk_score >= 70%,
    and schedules voice/SMS reminders for missed payments.
    """
    db = SessionLocal()
    called_phones = set()
    try:
        logger.info("Executing scheduled database-backed fraud checking job...")
        
        # 1. Purge any stale low-risk alerts (risk_score < 70) from DB to enforce clean threshold
        stale_low_risk = db.query(FraudAlert).filter(FraudAlert.risk_score < 70.0).all()
        if stale_low_risk:
            logger.info(f"Purging {len(stale_low_risk)} low-risk alert entries (< 70%) from DB")
            for sa in stale_low_risk:
                db.delete(sa)
            db.commit()

        # 2. Get unified aggregated agent risk scores
        agent_scores = compute_all_agent_risk_scores(db)
        if not agent_scores:
            logger.info("No agents found in database to evaluate.")
            return

        for agent in agent_scores:
            aid = agent["agent_id"]
            risk_score = agent["risk_score"]
            is_fraud = agent["is_fraud"]
            flag_reason = agent["flag_reason"]
            remittance_status = agent["status"]
            customer_phone = agent["customer_phone"]
            customer_lang = agent.get("language_pref", "english") or "english"

            # Trigger automated retry schedule if remittance_status == "missed"
            if remittance_status == "missed" and customer_phone:
                if customer_phone not in called_phones:
                    called_phones.add(customer_phone)
                    try:
                        logger.info(f"Triggering automated reminder retry schedule for customer {customer_phone} (Lang: {customer_lang})")
                        schedule_retry(
                            customer_phone=customer_phone,
                            agent_id=aid,
                            amount=agent["amount"],
                            language=customer_lang,
                            attempt=1
                        )
                    except Exception as ve:
                        logger.error(f"Voice reminder schedule retry failed: {str(ve)}")

            # Task 2: ONLY broadcast and persist if risk_score >= 70.0
            if risk_score >= 70.0:
                # Check if an active PENDING or INVESTIGATING alert already exists for this agent
                pending_alert = db.query(FraudAlert).filter(
                    FraudAlert.agent_id == aid,
                    FraudAlert.status.in_(["PENDING", "INVESTIGATING"])
                ).first()
                
                if not pending_alert:
                    now_dt = datetime.utcnow()
                    logger.info(f"High risk agent detected! Saving PENDING alert to DB: Agent {aid}, Score {risk_score:.1f}%")
                    
                    # Persist alert to database
                    alert_obj = FraudAlert(
                        agent_id=aid,
                        transaction_id=agent.get("latest_tx_id"),
                        risk_score=risk_score,
                        flag_reason=flag_reason,
                        branch=agent["branch"],
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
                        "agent_id": str(aid),
                        "risk_score": risk_score,
                        "risk_score_pct": f"{risk_score:.1f}%",
                        "is_fraud": is_fraud,
                        "flag_reason": flag_reason,
                        "status": "PENDING",
                        "timestamp": now_dt.isoformat() + "Z",
                        "created_at": now_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                    await broadcast_alert(alert_payload)
                else:
                    logger.info(f"Active alert for Agent {aid} already exists in DB. Suppressing duplicate creation.")
                    
    except Exception as e:
        logger.error(f"Exception raised in run_fraud_check_job: {str(e)}")
    finally:
        db.close()

# Add the job to fire every 5 minutes
scheduler.add_job(run_fraud_check_job, 'interval', minutes=5)
