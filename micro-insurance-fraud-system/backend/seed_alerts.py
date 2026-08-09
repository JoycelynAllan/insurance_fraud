from datetime import datetime
from backend.app.db import SessionLocal, engine, Base, auto_migrate_schema
from backend.app.models.alert import FraudAlert

# Ensure tables and columns exist
Base.metadata.create_all(bind=engine)
auto_migrate_schema()

db = SessionLocal()
try:
    print("--- STEP 5 SEEDING ALERTS ---")
    
    # 1. Seed AGT031
    existing_31 = db.query(FraudAlert).filter(FraudAlert.agent_id == "AGT031").first()
    if not existing_31:
        alert_31 = FraudAlert(
            agent_id="AGT031",
            transaction_id=1,
            risk_score=95.9,
            flag_reason="Risk score 95.9% — pending remittance with high cash ratio detected",
            status="PENDING",
            alerted_at=datetime.utcnow(),
            acknowledged=False
        )
        db.add(alert_31)
        print("Inserted PENDING alert for AGT031 (95.9%)")
    else:
        existing_31.risk_score = 95.9
        existing_31.flag_reason = "Risk score 95.9% — pending remittance with high cash ratio detected"
        existing_31.status = "PENDING"
        print("Updated PENDING alert for AGT031 (95.9%)")

    # 2. Seed AGT041
    existing_41 = db.query(FraudAlert).filter(FraudAlert.agent_id == "AGT041").first()
    if not existing_41:
        alert_41 = FraudAlert(
            agent_id="AGT041",
            transaction_id=2,
            risk_score=95.7,
            flag_reason="Risk score 95.7% — missed remittance flagged by ML model",
            status="PENDING",
            alerted_at=datetime.utcnow(),
            acknowledged=False
        )
        db.add(alert_41)
        print("Inserted PENDING alert for AGT041 (95.7%)")
    else:
        existing_41.risk_score = 95.7
        existing_41.flag_reason = "Risk score 95.7% — missed remittance flagged by ML model"
        existing_41.status = "PENDING"
        print("Updated PENDING alert for AGT041 (95.7%)")

    db.commit()
    print("Database seeding completed successfully.")
finally:
    db.close()
