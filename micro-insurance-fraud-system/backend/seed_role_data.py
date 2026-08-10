from datetime import datetime
from backend.app.db import SessionLocal, engine, Base, auto_migrate_schema
from backend.app.models.user import User
from backend.app.models.alert import FraudAlert
from backend.app.utils.auth_guard import hash_password

# Migrate database schema
Base.metadata.create_all(bind=engine)
auto_migrate_schema()

db = SessionLocal()
try:
    print("--- PART 8 SEEDING ROLE TEST DATA ---")
    
    # 1. Seed Supervisor Account
    sup = db.query(User).filter(User.email == "supervisor@mifds.gh").first()
    if not sup:
        sup = User(
            full_name="Accra Supervisor",
            email="supervisor@mifds.gh",
            password_hash=hash_password("Supervisor123!"),
            role="supervisor",
            branch="Accra",
            language_pref="english"
        )
        db.add(sup)
        db.commit()
        db.refresh(sup)
        print(f"Inserted Supervisor Account (ID: {sup.id}, Email: {sup.email})")
    else:
        sup.password_hash = hash_password("Supervisor123!")
        sup.role = "supervisor"
        sup.branch = "Accra"
        sup.language_pref = "english"
        db.commit()
        print(f"Updated Supervisor Account (ID: {sup.id}, Email: {sup.email})")

    # 2. Seed Agent Account
    agt = db.query(User).filter(User.email == "agent@mifds.gh").first()
    if not agt:
        agt = User(
            full_name="Tamale Agent",
            email="agent@mifds.gh",
            password_hash=hash_password("Agent123!"),
            role="agent",
            branch="Tamale",
            language_pref="dagbani",
            agent_id="AGT041"
        )
        db.add(agt)
        db.commit()
        db.refresh(agt)
        print(f"Inserted Agent Account (ID: {agt.id}, Email: {agt.email}, AgentID: {agt.agent_id})")
    else:
        agt.password_hash = hash_password("Agent123!")
        agt.role = "agent"
        agt.branch = "Tamale"
        agt.language_pref = "dagbani"
        agt.agent_id = "AGT041"
        db.commit()
        print(f"Updated Agent Account (ID: {agt.id}, Email: {agt.email}, AgentID: {agt.agent_id})")

    # 3. Seed Fraud Alerts
    alert_31 = db.query(FraudAlert).filter(FraudAlert.agent_id == "AGT031").first()
    if not alert_31:
        alert_31 = FraudAlert(
            agent_id="AGT031",
            transaction_id=1,
            risk_score=95.9,
            flag_reason="Risk score 95.9% — pending remittance with high cash ratio",
            status="PENDING",
            alerted_at=datetime.utcnow(),
            acknowledged=False
        )
        db.add(alert_31)
        db.commit()
        db.refresh(alert_31)
        print(f"Inserted Fraud Alert AGT031 (ID: {alert_31.id})")
    else:
        alert_31.risk_score = 95.9
        alert_31.status = "PENDING"
        alert_31.flag_reason = "Risk score 95.9% — pending remittance with high cash ratio"
        db.commit()
        print(f"Updated Fraud Alert AGT031 (ID: {alert_31.id})")

    alert_41 = db.query(FraudAlert).filter(FraudAlert.agent_id == "AGT041").first()
    if not alert_41:
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
        db.commit()
        db.refresh(alert_41)
        print(f"Inserted Fraud Alert AGT041 (ID: {alert_41.id})")
    else:
        alert_41.risk_score = 95.7
        alert_41.status = "PENDING"
        alert_41.flag_reason = "Risk score 95.7% — missed remittance flagged by ML model"
        db.commit()
        print(f"Updated Fraud Alert AGT041 (ID: {alert_41.id})")

    print(f"All inserted IDs: Supervisor ID={sup.id}, Agent ID={agt.id}, Alert1 ID={alert_31.id}, Alert2 ID={alert_41.id}")
finally:
    db.close()
