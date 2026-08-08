## Phase 15 — Fix Registration Exception & Duplicate Commit Handling (Week 19)

### Root Cause Analysis
1. **Contradictory Log Sequences (Success followed by Error):**
   - Occurred when an email registration was retried or resubmitted (e.g., via browser form double-click or request retry). The initial request succeeded (`[DB REGISTER SUCCESS]`), inserting the email into `public.users`.
   - Subsequent registration requests with the same email bypassed the initial `db.query(User)` check due to casing/whitespace differences or session transaction cache states, proceeding to `db.commit()`.
   - PostgreSQL's `users_email_key` unique constraint threw `IntegrityError` (`psycopg2.errors.UniqueViolation`), causing `[DB REGISTER ERROR]` and a 500 status code response instead of a clean 400 Bad Request response.

---

### What Was Built
- **Case-Insensitive Email Normalization ([`auth.py`](file:///c:/Users/Apoka/Downloads/investment_project/micro-insurance-fraud-system/backend/app/routes/auth.py)):**
  - Added email cleaning and lowercasing (`clean_email = body.email.strip().lower()`).
  - Updated pre-check query to use `func.lower(User.email) == clean_email`.
- **Explicit `IntegrityError` Handling:**
  - Added explicit `except IntegrityError as ie:` block catching database unique constraint violations and returning a clean 400 Bad Request (`detail="Email already registered"`).
- **Full Traceback Logging:**
  - Added `exc_info=True` on general `except Exception as e:` logging to capture complete un-truncated tracebacks.

---

### Verification
- Python syntax compiled successfully for `backend/app/routes/auth.py`.
- Verified single, deterministic commit path with explicit duplicate error handling.
