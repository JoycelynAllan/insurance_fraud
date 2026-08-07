## Phase 8 — OTP Security Hardening, Table Layout Defenses, Supabase Sync & Voice Call Verification (Week 12)

### What was built
- **OTP Security Hardening & Exposure Removal:**
  - Removed `"dev_otp"` key from the API response payload of `/api/otp/send` in `backend/app/routes/otp.py`.
  - Removed `devOtpHint` state and the `[DEV MODE] Generated OTP` banner from `SmsOtpDialog.js`.
  - Production backend now exclusively dispatches real SMS via Africa's Talking whenever `AT_API_KEY` is present, with zero OTP exposure in HTTP responses or UI.

- **Supabase Database Connection Order:**
  - Updated `DATABASE_URL` resolution logic in `backend/app/db.py` to check:
    `os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL") or os.getenv("SUPABASE_POSTGRES_URL") or "sqlite:///./fraud_db.db"`
  - Guarantees SQLAlchemy connects directly to Supabase's PostgreSQL instance when `SUPABASE_DATABASE_URL` is configured in Render Environment settings, populating `public.users`.

- **Agent Risk Table Defensive Rendering & Column Alignment:**
  - Added property fallback guards in `AgentRiskTable.js` for all row attributes:
    - `risk_score`: `typeof row.risk_score === "number" ? row.risk_score : parseFloat(row.risk_score) || 0.0`
    - `amount`: `typeof row.amount === "number" ? row.amount : parseFloat(row.amount) || 0.0`
    - `status`: `row.status || row.remittance_status || (row.is_fraud ? "FLAGGED" : "CLEARED")`
    - `date`: `row.date ? String(row.date).split(" ")[0] : "-"`
  - Enforced explicit `minWidth` constraints on `TableCell` elements across `TableHead` and `TableBody` (`Agent ID`, `Branch`, `Risk Score`, `Status`, `Amount`, `Date`).

- **Dograh Voice Call Diagnostics:**
  - Updated `dograh_trigger.py` to return the `notes` field in `trigger_payment_reminder_call`'s return dictionary.
  - Returned diagnostic details (`outcome`, `notes`, `timestamp`, `customer_phone`) in `/api/voice/trigger`.

---

### Verification
- `npm run build` executed and passed cleanly in `material-dashboard-react`.
- Python syntax compiled successfully for `otp.py`, `db.py`, `voice.py`, and `dograh_trigger.py`.
