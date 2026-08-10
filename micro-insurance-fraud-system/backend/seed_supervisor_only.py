from backend.app.db import SessionLocal, engine, Base, auto_migrate_schema
from backend.app.models.user import User
from backend.app.utils.auth_guard import hash_password

# Initialize & Migrate Schema
Base.metadata.create_all(bind=engine)
auto_migrate_schema()

db = SessionLocal()
try:
    print("--- PART 1 & 14 DATABASE CLEANUP AND SUPERVISOR SEEDING ---")
    
    # 1. Purge any non-supervisor / non-admin user rows
    purged_count = db.query(User).filter(User.role.in_(["agent", "risk_officer"])).delete(synchronize_session=False)
    db.commit()
    print(f"Purged {purged_count} agent/risk_officer accounts from public.users.")

    # 2. Seed Test Supervisor Account
    sup = db.query(User).filter(User.email == "supervisor@mifds.gh").first()
    if not sup:
        sup = User(
            full_name="Test Supervisor",
            email="supervisor@mifds.gh",
            password_hash=hash_password("Supervisor123!"),
            role="supervisor",
            branch="Accra",
            language_pref="english"
        )
        db.add(sup)
        db.commit()
        db.refresh(sup)
        print(f"Inserted Test Supervisor (ID: {sup.id}, Email: {sup.email}, Role: {sup.role})")
    else:
        sup.full_name = "Test Supervisor"
        sup.password_hash = hash_password("Supervisor123!")
        sup.role = "supervisor"
        sup.branch = "Accra"
        db.commit()
        print(f"Updated Test Supervisor (ID: {sup.id}, Email: {sup.email}, Role: {sup.role})")

    print(f"Inserted/Updated Supervisor ID: {sup.id}")
finally:
    db.close()
