## Missed Payment Voice Call Flow

### Trigger conditions
- Fraud score >= 70
- remittance_status == "missed"

### Call flow
1. Scheduler job fires (every 5 minutes)
2. Rows scored via score_transaction()
3. Fraud + missed condition detected
4. trigger_payment_reminder_call() invoked
5. Dograh connects to telephony provider
6. Outbound call placed to customer_phone
7. Script delivered if answered
8. Outcome logged to call_logs.db
9. If no_answer: schedule_retry() queued for T+2h
10. Max 3 attempts per customer per fraud event

### Outcome states
| Outcome    | Next action                        |
|------------|------------------------------------|
| answered   | Log success, no retry              |
| no_answer  | Retry in 2h (max 3 attempts)       |
| failed     | Log failure, alert dashboard       |

### Telephony provider
- Primary: Dograh (localhost:3000)
- Underlying: Africa's Talking (African local SMS/voice provider for local delivery)

### Known issues & resolutions
- **Docker Daemon Inactive**: Ensure Docker Desktop is open and active before running the docker container stacks.
- **Port 8000 Collision**: The Dograh API container binds to port 8000. Ensure the micro-insurance FastAPI backend runs on a different port (e.g., 8001 or 5000) if run on the same interface, or map Dograh container port to 8000 while our backend runs on 8001.
- **Outbound Calling Latency**: Polling the REST runs API endpoints of Dograh has a 30-second timeout to handle async webhook callbacks correctly.
