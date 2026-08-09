## Missed Payment Voice Call Flow

### Trigger conditions
- Fraud score >= 70 (or manual trigger from dashboard)
- remittance_status == "missed"

### Call flow
1. Outbound call triggered via `make_outbound_call()` in `voice_service.py` (`POST https://voice.africastalking.com/call`).
2. Customer `language_pref` ('twi' or 'dagbani') resolved and stored in Supabase `voice_call_logs`.
3. Africa's Talking places outbound call to `customer_phone`.
4. On call connect (Stage 1), AT hits registered callback endpoint `POST /api/voice/callback`.
5. Callback handler responds with XML `<GetDigits>` playing language-appropriate reminder MP3 template (`twi_reminder.mp3` or `dagbani_reminder.mp3`).
6. On DTMF Keypress (Stage 2):
   - Key 1 pressed: Logs `payment_confirmed_by_customer`, updates associated `fraud_alerts` status to `RESOLVED`, plays confirmation audio (`twi_confirm.mp3` or `dagbani_confirm.mp3`).
   - Key 2 pressed: Logs `transfer_to_support_requested`, connects customer to support representative.
7. On call end (Stage 3): AT posts final call metrics (`durationInSeconds`, `recordingUrl`, `currencyCode`, `amount`), updating `voice_call_logs` in Supabase PostgreSQL.

### Outcome states
| Outcome | Description & Next Action |
|:---|:---|
| `queued` | Outbound call successfully dispatched to AT Voice Gateway |
| `payment_confirmed_by_customer` | Customer pressed key 1; fraud alert updated to RESOLVED |
| `transfer_to_support_requested` | Customer pressed key 2; support transfer logged |
| `no_answer` / `completed` | Call completed without keypress or ended |
| `failed` | Destination unsupported or invalid phone number |

### Telephony provider
- **Provider:** Africa's Talking Voice Gateway (`voice.africastalking.com`)
- **Callback Endpoint:** `POST /api/voice/callback` (`Content-Type: text/plain`)
- **Voice Templates:** Multilingual Twi & Dagbani gTTS MP3 files hosted in `/static/audio` and raw storage

### Deployment Requirement
Once deployed on Render, register your AT Voice number and set the Callback URL in the Africa's Talking Voice Dashboard to:
`https://investment-project-3.onrender.com/api/voice/callback`
