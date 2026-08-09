## Phase 19 — Fix Startup Crash: Remove Leftover Dograh Imports from Scheduler & Pipeline (Week 23)

### Root Cause Analysis
- During backend boot, `main.py` initializes `scheduler.py` via `lifespan`.
- `scheduler.py` (line 9) and `backend/tests/test_pipeline.py` (line 21) still contained leftover imports: `from voice.dograh_trigger import trigger_payment_reminder_call`.
- Because `voice/dograh_trigger.py` imported `dograh_sdk` at top-level module load time, removing `dograh-sdk` from `requirements.txt` in Phase 17 caused an unhandled `ModuleNotFoundError: No module named 'dograh_sdk'`, crashing backend startup on boot.

---

### What Was Built
- **Scheduler Update ([`scheduler.py`](file:///c:/Users/Apoka/Downloads/investment_project/micro-insurance-fraud-system/backend/app/services/scheduler.py)):**
  - Replaced `from voice.dograh_trigger import trigger_payment_reminder_call` with `from backend.app.services.voice_service import make_outbound_call`.
  - Updated scheduled fraud check outbound voice trigger to invoke `make_outbound_call(customer_phone=..., agent_id=..., amount=...)`.

- **Test Pipeline Update ([`test_pipeline.py`](file:///c:/Users/Apoka/Downloads/investment_project/micro-insurance-fraud-system/backend/tests/test_pipeline.py)):**
  - Updated `test_pipeline.py` to import `make_outbound_call` and query Supabase PostgreSQL `VoiceCallLog` records.

- **Full Workspace Audit:**
  - Audited codebase and verified 0 remaining active imports of `dograh_trigger` or `dograh_sdk`.

---

### Verification
- Python syntax compiled successfully for `main.py`, `scheduler.py`, `voice_service.py`, and `test_pipeline.py`.
- Verified backend boot sequence proceeds without `ModuleNotFoundError` crashes.
