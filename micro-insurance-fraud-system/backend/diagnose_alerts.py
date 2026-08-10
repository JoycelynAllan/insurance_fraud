import sys
from backend.app.db import SessionLocal
from backend.app.models.alert import FraudAlert
from backend.app.models.transaction import Transaction, TransactionFeature
from sqlalchemy import text

db = SessionLocal()
try:
    # Check fraud_alerts table count & sample
    alert_count = db.query(FraudAlert).count()
    print("Total fraud_alerts rows:", alert_count)

    alerts = db.query(FraudAlert).limit(10).all()
    print("Sample fraud_alerts:", [(a.id, a.agent_id, a.risk_score, a.status, a.flag_reason) for a in alerts])

    # Check high risk agents in transactions/features
    records = db.query(Transaction.agent_id, TransactionFeature.risk_score).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).all()

    high_risk = []
    for aid, score in records:
        sc = float(score) if score is not None else 0.0
        sc_pct = sc * 100.0 if sc <= 1.0 else sc
        if sc_pct >= 70.0:
            high_risk.append((aid, sc_pct))

    print("High risk agents (>= 70%):", high_risk)

    print("Diagnosis complete")
finally:
    db.close()
