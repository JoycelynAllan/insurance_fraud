## Phase 14 — Fix Schema Migration & CORS-Preserving Exception Handling (Week 18)

### Root Cause Analysis
1. **Database Schema Mismatch on Pre-existing Tables:**
   - `Base.metadata.create_all(bind=engine)` creates missing tables, but **never alters pre-existing tables** to add new columns.
   - When new columns (`phone_number`, `phone_verified`, `branch`, `last_login`) were added to the `User` model, pre-existing `public.users` tables on Supabase PostgreSQL produced `psycopg2.errors.UndefinedColumn` crashes during registration `INSERT` queries.

2. **Uncaught 500 Exceptions Masking as CORS Blocks:**
   - Unhandled 500 exceptions in FastAPI returned standard error responses before Starlette's `CORSMiddleware` attached `Access-Control-Allow-Origin` headers, causing browsers to report 500 errors as CORS blocks.

---

### What Was Built
- **Automatic Schema Migration Helper (`auto_migrate_schema` in `db.py`):**
  - Added `auto_migrate_schema()` in `db.py`, called automatically during application boot in `lifespan`.
  - Idempotently executes `ALTER TABLE public.users ADD COLUMN IF NOT EXISTS ...` queries on Supabase PostgreSQL for `phone_number`, `phone_verified`, `branch`, and `last_login`.

- **CORS-Preserving Global Exception Handler (`main.py`):**
  - Registered `@app.exception_handler(Exception)` in `main.py`.
  - Guarantees `Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials` headers are attached to all 500/400 error responses, allowing true diagnostic messages to display cleanly in browser consoles.

---

### Verification
- Python syntax compiled successfully for `backend/app/db.py` and `backend/app/main.py`.
- Schema auto-migration and global CORS exception handlers active.
