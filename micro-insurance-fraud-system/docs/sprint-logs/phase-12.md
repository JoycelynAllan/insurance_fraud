## Phase 12 — Tracing & Diagnosing Database Persistence for Registration (Week 16)

### Investigation & Root Cause Findings
1. **Resolved Database Engine Host:**
   - On Render, `db.py` resolves `DATABASE_URL`, `SUPABASE_DATABASE_URL`, or `SUPABASE_POSTGRES_URL`.
   - Added explicit boot-time logging: `[DB RUNTIME CONFIG] Resolved Database Connection URL: postgresql://***:***@db.xvykfctqxsnttiibxvyu.supabase.co:5432/postgres`.
   - **Root Cause Identified:** If Render's environment variable `DATABASE_URL` is omitted or unconfigured in Render's dashboard, `db.py` fell back to `sqlite:///./fraud_db.db` inside the ephemeral container. The registration endpoint inserted into container-local SQLite `fraud_db.db` and committed successfully (returning 201 Created), but Supabase PostgreSQL project `xvykfctqxsnttiibxvyu` received no queries.

2. **Session Commit Verification (`auth.py`):**
   - Verified that `db.add(new_user)` is immediately followed by `db.commit()` and `db.refresh(new_user)`.
   - Added explicit logger diagnostics and try/rollback/except handling:
     `logger.info(f"[DB REGISTER SUCCESS] User '{new_user.email}' (ID: {new_user.id}) inserted and committed successfully.")`

3. **Single Handler Verification:**
   - Verified that `backend/app/routes/auth.py` is the single, authoritative registration route registered under `/api/auth/register`.

---

### Verification Checklist
- Python syntax compiled successfully for `db.py` and `auth.py`.
- Runtime database URL host logging active at application startup.
