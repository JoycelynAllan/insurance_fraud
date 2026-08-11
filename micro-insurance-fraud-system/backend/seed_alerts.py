from datetime import datetime
from backend.app.db import SessionLocal
from backend.app.models.alert import FraudAlert
from backend.app.routes.agents import compute_all_agent_risk_scores

db = SessionLocal()
try:
    print("--- SEEDING PENDING FRAUD ALERTS FOR HIGH RISK AGENTS ---")

    # Purge any low-risk alerts (< 70%)
    low_risk = db.query(FraudAlert).filter(FraudAlert.risk_score < 70.0).all()
    if low_risk:
        print(f"Purging {len(low_risk)} low-risk alert rows (< 70%) from database...")
        for lr in low_risk:
            db.delete(lr)
        db.commit()

    agent_scores = compute_all_agent_risk_scores(db)
    high_risk_agents = [a for a in agent_scores if a["risk_score"] >= 70.0]

    print(f"Found {len(high_risk_agents)} high-risk agents (>= 70%) using aggregated feature scoring")

    inserted_count = 0
    for agent in high_risk_agents:
        aid = agent["agent_id"]
        risk_score = agent["risk_score"]

        # Check if PENDING or INVESTIGATING alert already exists
        existing = db.query(FraudAlert).filter(
            FraudAlert.agent_id == aid,
            FraudAlert.status.in_(["PENDING", "INVESTIGATING"])
        ).first()

        if existing:
            print(f"Active alert already exists for Agent {aid} (Status: {existing.status}, Score: {existing.risk_score}%) — updating score")
            existing.risk_score = risk_score
            continue

        new_alert = FraudAlert(
            agent_id=aid,
            transaction_id=agent.get("latest_tx_id"),
            risk_score=risk_score,
            flag_reason=agent["flag_reason"],
            branch=agent["branch"],
            status="PENDING",
            alerted_at=datetime.utcnow(),
            acknowledged=False
        )
        db.add(new_alert)
        inserted_count += 1
        print(f"Inserted PENDING alert for {aid} at {risk_score:.1f}%")

    db.commit()
    print(f"Done seeding alerts! Total new PENDING alerts inserted: {inserted_count}")

    # Print current active alerts summary
    active_alerts = db.query(FraudAlert).filter(FraudAlert.status.in_(["PENDING", "INVESTIGATING"])).all()
    print(f"Active PENDING/INVESTIGATING alerts in DB now: {len(active_alerts)}")
    for a in active_alerts:
        print(f" - Alert ID {a.id}: Agent {a.agent_id}, Score {a.risk_score}%, Status {a.status}")

finally:
    db.close()
