## Phase 17 — Africa's Talking Voice Gateway Migration, Multilingual Audio, IVR Keypress, & Alert Acknowledgement (Week 21)

### What Was Built
- **Dograh Deprecation & Cleanup:**
  - Removed `voice/dograh_trigger.py` and `dograh-sdk` dependency.
  - Retained and upgraded `voice_call_logs` table schema in Supabase PostgreSQL.

- **Africa's Talking Outbound Voice Service ([`voice_service.py`](file:///c:/Users/Apoka/Downloads/investment_project/micro-insurance-fraud-system/backend/app/services/voice_service.py)):**
  - Implemented `make_outbound_call` sending HTTP POST to Africa's Talking Voice API (`POST https://voice.africastalking.com/call` or `https://voice.sandbox.africastalking.com/call`).
  - Added headers (`apiKey`, `Content-Type: application/x-www-form-urlencoded`), username, source voice number (`from`), target phone (`to`), and `clientRequestId`.
  - Parsed API status (`Queued`, `InvalidPhoneNumber`, `DestinationNotSupported`, `InsufficientCredit`) and stored call session details in `public.voice_call_logs`.

- **Multilingual Audio Template Generation (`gTTS`):**
  - Installed `gTTS` (`python-multipart` & `gTTS` added to `requirements.txt`).
  - Authored `generate_audio.py` to produce MP3 voice templates in `backend/app/voice/audio/`:
    - `twi_reminder.mp3`: *"Mema wo akye. Wo insurance premium bi nte hɔ. Yɛsrɛ wo, fa sika no kɔ wo agent nkyɛn."*
    - `twi_confirm.mp3`: *"Meda wo ase. Yɛbɛ bo w'adwuma ho ban."*
    - `dagbani_reminder.mp3`: *"N bɔri n lɔri. A insurance puuni bi ka. Shɛri ni fo agent ka amoonin."*
    - `dagbani_confirm.mp3`: *"Mpayi. Ti ni fa a tuma gbahin."*
  - Exposed audio files via static mount (`/static/audio`) and raw GitHub URLs.

- **Single Callback IVR Endpoint ([`voice_callback.py`](file:///c:/Users/Apoka/Downloads/investment_project/micro-insurance-fraud-system/backend/app/routes/voice_callback.py)):**
  - Implemented `POST /api/voice/callback` returning `Content-Type: text/plain` XML `<Response>...</Response>`.
  - **Stage 1 (Call Connected):** Rendered `<GetDigits timeout="10" finishOnKey="#"><Play url="[REMINDER_URL]"/></GetDigits>`.
  - **Stage 2 (DTMF IVR Response):**
    - If `dtmfDigits == "1"`: Logged `payment_confirmed_by_customer`, updated associated `FraudAlert` status to `RESOLVED`, played `confirm` audio.
    - If `dtmfDigits == "2"`: Logged `transfer_to_support_requested`, played support prompt.
  - **Stage 3 (Call Ended):** Updated `duration_seconds`, `recording_url`, `currency_code`, `call_amount`, and marked outcome in Supabase `voice_call_logs`.

- **Alert Acknowledgement Endpoint ([`alerts.py`](file:///c:/Users/Apoka/Downloads/investment_project/micro-insurance-fraud-system/backend/app/routes/alerts.py)):**
  - Added `GET /api/alerts` to query fraud alerts from Supabase.
  - Added `POST /api/alerts/{alert_id}/acknowledge` to set alert status to `INVESTIGATING` or `RESOLVED` with user attribution from JWT.

---

### Verification
- `gTTS` audio generation script executed and produced all 4 MP3 templates.
- Python syntax compiled successfully for all backend models, services, and routers.
- TestClient simulation verified 200 OK responses, `text/plain` headers, and valid XML output across Stage 1, Stage 2 (DTMF 1), and Stage 3.
