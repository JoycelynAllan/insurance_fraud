from backend.app.db import SessionLocal, engine, Base, auto_migrate_schema
import backend.app.models

# Ensure tables and columns are migrated locally and remotely
Base.metadata.create_all(bind=engine)
auto_migrate_schema()

db = SessionLocal()

print("--- STEP 1 DIAGNOSTICS ---")

# 1. Query public.fraud_alerts count and first 5 rows
from backend.app.models.alert import FraudAlert
alerts_count = db.query(FraudAlert).count()
print(f"1. public.fraud_alerts row count: {alerts_count}")
alerts = db.query(FraudAlert).limit(5).all()
for a in alerts:
    print(f"   Alert ID: {a.id}, Agent: {a.agent_id}, Risk: {a.risk_score}, Status: {a.status}, Flag Reason: {a.flag_reason}")

# 2. Query risk_score for AGT031 and AGT041 from Transaction/TransactionFeature
from backend.app.models.transaction import Transaction, TransactionFeature
for aid in ["AGT031", "AGT041"]:
    rec = db.query(Transaction, TransactionFeature).join(
        TransactionFeature, Transaction.id == TransactionFeature.transaction_id
    ).filter(Transaction.agent_id == aid).order_by(Transaction.timestamp.desc()).first()
    if rec:
        tx, feat = rec
        print(f"2. Agent {aid}: Risk Score = {feat.risk_score}, Status = {tx.remittance_status}, Flag Reason = {feat.flag_reason}")
    else:
        print(f"2. Agent {aid}: No transaction record found.")

db.close()
