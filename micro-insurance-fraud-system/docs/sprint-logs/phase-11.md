## Phase 11 — Enforce Supabase as Single Source of Truth for ALL App Data (Week 15)

### What was built
- **Full Backend Data Persistence Audit:**
  - Audited all application data entities and confirmed that registration, authentication, sessions, OTP codes, agent risk metrics, fraud alerts, transactions, and voice campaign call logs persist exclusively in Supabase PostgreSQL via SQLAlchemy.
  - Eliminated local SQLite `.db` files (`call_logs.db`, `fraud_db.db`) and removed fallback SQLite creation logic.

- **Voice Call Logs Supabase Migration:**
  - Created `VoiceCallLog` SQLAlchemy model in `backend/app/models/voice.py` (`__tablename__ = "voice_call_logs"`).
  - Updated `_log_attempt` in `voice/dograh_trigger.py` to instantiate and save `VoiceCallLog` records directly to Supabase PostgreSQL using `SessionLocal()`.
  - Migrated `/api/voice/logs` in `backend/app/routes/voice.py` to query `db.query(VoiceCallLog)` on Supabase PostgreSQL.
  - Registered `VoiceCallLog` in `models/__init__.py` so `Base.metadata.create_all(bind=engine)` automatically creates `public.voice_call_logs` on Supabase PostgreSQL at application startup.

- **Session & User Persistence Architecture:**
  - Authenticated sessions write to `public.sessions` and are validated against Supabase PostgreSQL on every request via `get_current_user`.
  - Confirmed custom JWT authentication writing directly to `public.users` (including `role`, `branch`, `phone_number`, `phone_verified`), maintaining complete control over roles and foreign key relationships to agents and alerts.

---

### App Persistence Matrix

| Entity | Primary Table Name | Storage Engine | Access Mechanism |
| :--- | :--- | :--- | :--- |
| **Users** | `public.users` | Supabase PostgreSQL | `db.query(User)` via SQLAlchemy |
| **Sessions** | `public.sessions` | Supabase PostgreSQL | `db.query(UserSession)` via SQLAlchemy |
| **OTP Codes** | `public.otp_codes` | Supabase PostgreSQL | `db.query(OTPCode)` via SQLAlchemy |
| **Agents** | `public.agents` | Supabase PostgreSQL | `db.query(Agent)` via SQLAlchemy |
| **Transactions** | `public.transactions` | Supabase PostgreSQL | `db.query(Transaction)` via SQLAlchemy |
| **Features** | `public.transaction_features` | Supabase PostgreSQL | `db.query(TransactionFeature)` via SQLAlchemy |
| **Fraud Alerts** | `public.fraud_alerts` | Supabase PostgreSQL | `db.query(FraudAlert)` via SQLAlchemy |
| **Voice Call Logs** | `public.voice_call_logs` | Supabase PostgreSQL | `db.query(VoiceCallLog)` via SQLAlchemy |

---

### Verification
- `npm run build` executed and passed cleanly in `material-dashboard-react`.
- Python syntax compiled successfully for `models/voice.py`, `models/__init__.py`, `voice/dograh_trigger.py`, `routes/voice.py`, and `main.py`.
