## Phase 4 — Voice Automation (Week 8)

### What was built
- Installed `dograh-sdk` and added it to python dependencies in `requirements.txt`.
- Configured the React app to start on port `3001` in `package.json` to prevent port collisions with Dograh.
- Created `voice/dograh_trigger.py` implementing SQLite3 call logs logging (`call_logs.db`), client outbound triggering via Dograh Client (`test_phone_call`), and recursive 2-hour retry job scheduling up to 3 attempts.
- Wired the voice calling trigger safely into `run_fraud_check_job` in `backend/app/services/scheduler.py` with deduplication per run and isolated `try/except` error boundaries.
- Documented call workflows at `voice/workflows/missed_payment_flow.md`.

### Dograh setup notes
- **Docker Compose Startup**: Starting Dograh via `docker compose up` requires Docker Desktop daemon to be running.
- **Port Conflict**: To resolve conflicts, the React development frontend server was shifted to port `3001`. The FastAPI server runs on port `8001` to allow Dograh's API container to run on port `8000`.

### Africa's Talking telephony integration
- **Connection Model**: Dograh routes outbound calls through the Africa's Talking provider adapter using configured credentials from the user's organization in the Dograh dashboard.
- **Ghanaian Phone Numbers (+233)**: Africa's Talking requires E.164 formatting for all destination numbers. Ensure that customer phone numbers are stored with the proper prefix (e.g. `+233...`) to route calls correctly across Ghanaian telecom networks.

### Voice trigger integration with fraud scheduler
- **Wired Location**: Trigger is fired inside the `scheduler.py` loop after scoring transactions.
- **Deduplication**: A `called_phones` set tracks phone numbers called during the job run to prevent duplicate call triggers for a single customer.
- **Error Handling**: Firing the call is wrapped in a `try/except` block, ensuring network or integration failures with Dograh never abort or crash the main database scheduled job.

### Open items / known limitations
- Polling for call outcomes (such as `answered`, `no_answer`, `failed`) is done synchronously on call initiation to log the final callback state. The polling process runs in a background thread for scheduled retries to avoid blocking the main async scheduler thread loop.
