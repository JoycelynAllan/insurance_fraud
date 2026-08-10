from datetime import datetime
from backend.app.db import SessionLocal
from backend.app.models.alert import FraudAlert
from backend.app.models.transaction import Transaction, TransactionFeature

db = SessionLocal()
try:
    print("--- SEEDING PENDING FRAUD ALERTS FOR HIGH RISK AGENTS ---")

    # Get latest transaction & feature per agent
    records = db.query(Transaction, TransactionFeature).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).all()

    agent_latest = {}
    for tx, feat in records:
        aid = tx.agent_id
        if aid not in agent_latest or tx.timestamp > agent_latest[aid][0].timestamp:
            agent_latest[aid] = (tx, feat)

    high_risk_agents = []
    for aid, (tx, feat) in agent_latest.items():
        score = float(feat.risk_score) if feat.risk_score is not None else 0.0
        score_pct = score * 100.0 if score <= 1.0 else score
        if score_pct >= 70.0:
            high_risk_agents.append((aid, score_pct, tx, feat))

    print(f"Found {len(high_risk_agents)} high-risk agents (>= 70%)")

    inserted_count = 0
    for aid, score_pct, tx, feat in high_risk_agents:
        # Check if PENDING or INVESTIGATING alert already exists
        existing = db.query(FraudAlert).filter(
            FraudAlert.agent_id == aid,
            FraudAlert.status.in_(["PENDING", "INVESTIGATING"])
        ).first()

        if existing:
            print(f"Active alert already exists for Agent {aid} (Status: {existing.status}) — skipping")
            continue

        reason = feat.flag_reason or f"Risk score {score_pct:.1f}% — automated ML detection"
        new_alert = FraudAlert(
            agent_id=aid,
            transaction_id=tx.id,
            risk_score=score_pct,
            flag_reason=reason,
            branch=tx.branch,
            status="PENDING",
            alerted_at=datetime.utcnow(),
            acknowledged=False
        )
        db.add(new_alert)
        inserted_count += 1
        print(f"Inserted PENDING alert for {aid} at {score_pct:.1f}%")

    db.commit()
    print(f"Done seeding alerts! Total new PENDING alerts inserted: {inserted_count}")

    # Print current active alerts summary
    active_alerts = db.query(FraudAlert).filter(FraudAlert.status.in_(["PENDING", "INVESTIGATING"])).all()
    print(f"Active PENDING/INVESTIGATING alerts in DB now: {len(active_alerts)}")
    for a in active_alerts:
        print(f" - Alert ID {a.id}: Agent {a.agent_id}, Score {a.risk_score}%, Status {a.status}")

finally:
    db.close()
