# MicroInsure Fraud Detection System — Comprehensive System Documentation

## Executive Overview
The **MicroInsure Fraud Detection System** is an enterprise-grade micro-insurance fraud monitoring, anomaly detection, and automated enforcement platform. It combines high-performance machine learning (Isolation Forest + XGBoost), dual-channel telephony automation (Africa's Talking SMS OTP & Dograh AI Outbound Conversational Voice), and real-time risk reporting to safeguard micro-insurance remittances across regional branch offices in Ghana.

---

## 🏗️ System Architecture & Technology Stack

```
                               ┌────────────────────────────────────────────────────────┐
                               │     React Frontend (Material Dashboard 2 UI)           │
                               │     Hosted on Render Static Site                        │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │ REST API / WebSockets
                                                          ▼
                               ┌────────────────────────────────────────────────────────┐
                               │     FastAPI Backend Engine                              │
                               │     Hosted on Render Web Service                       │
                               └──────┬───────────────────┬───────────────────┬─────────┘
                                      │                   │                   │
                                      ▼                   ▼                   ▼
           ┌─────────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
           │   Supabase PostgreSQL DB    │ │  Dograh Conversational  │ │  Africa's Talking SDK   │
           │ (Single Source of Truth)    │ │  AI Outbound Voice      │ │     SMS OTP Engine      │
           └─────────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
```

### Core Technologies
1. **Frontend:** React 18, Material UI (MUI 5), Axios, Emotion, React Router 6.
2. **Backend:** FastAPI (Python 3.10+), SQLAlchemy ORM, Pydantic, APScheduler, Uvicorn.
3. **Machine Learning:** Scikit-Learn (Isolation Forest), XGBoost Classifier, Joblib Preprocessing.
4. **Database:** Supabase PostgreSQL (`db.xvykfctqxsnttiibxvyu.supabase.co:5432`) as the single source of truth for all application state.
5. **Telephony & Outbound Voice:**
   - **SMS OTP Verification:** Africa's Talking SMS Gateway API.
   - **Conversational Voice AI:** Dograh AI Outbound Voice Platform (Workflow `9611` - "PSTN - outbound") integrated with Vonage Telephony (Config `963`).

---

## 📊 Data Sources & Persistence Model

Every piece of data used and displayed by the system originates from **Supabase PostgreSQL**. The table below documents where each data type is stored and managed:

| Data Type | Primary Supabase Table | Description & Source |
| :--- | :--- | :--- |
| **User Accounts** | `public.users` | Stores registered analysts and admins, full names, hashed passwords, roles (`analyst`, `admin`), branch bindings (`Accra`, `Kumasi`, `Tamale`, `Takoradi`, `Cape Coast`), phone numbers, and verification statuses. |
| **User Sessions** | `public.sessions` | Stores active JWT bearer tokens, issue timestamps, and expiration times. Validated against Supabase on every API request. |
| **OTP Verification Codes** | `public.otp_codes` | Stores generated 6-digit SMS OTP verification codes, expiration windows (5 mins), and usage flags (`is_used`). |
| **Agent Risk Profiles** | `public.agents` | Stores micro-insurance agent IDs, assigned branch office, cumulative risk scores (0.00 – 1.00), risk status (`CLEARED`, `FLAGGED`, `CRITICAL`), total remittance amounts, and last transaction dates. Seeding engine (`seed_db.py`) populates initial synthetic records if empty on startup. |
| **Remittance Transactions** | `public.transactions` | Stores raw transaction events, customer phone numbers, remittance amounts, policy numbers, and timestamps. |
| **ML Feature Vectors** | `public.transaction_features` | Stores computed feature values used by the machine learning engine: `remittance_delay_days`, `amount_deviation`, `claim_frequency`, and `velocity_score`. |
| **Fraud Alerts** | `public.fraud_alerts` | Stores triggered anomaly alerts, risk severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), confidence scores, and review statuses (`PENDING`, `INVESTIGATING`, `RESOLVED`). |
| **Voice Campaign Logs** | `public.voice_call_logs` | Stores outbound AI voice call attempts, target phone numbers, agent IDs, remittance amounts, call outcomes (`answered`, `no_answer`, `failed`), attempt counters, and diagnostic error notes. |

---

## ✨ Key Features & Capabilities

### 1. Real-Time Anomaly Detection & Machine Learning Inference
- **Isolation Forest Classifier:** Unsupervised anomaly detection model trained to identify statistical outliers in remittance velocity, delay days, and claim frequencies.
- **XGBoost Classifier:** Supervised gradient boosting classifier that computes precise fraud probability scores for each agent and transaction.
- **Automated Alert Generation:** High-risk transactions (risk score > `0.70`) automatically trigger fraud alerts saved in `public.fraud_alerts`.

### 2. MicroInsure Agent Risk Monitoring Dashboard
- **Agent Risk Profiles Table:** Interactive data grid displaying Agent ID, Branch Office, Risk Score badge, Status pill (`CLEARED` / `FLAGGED`), Total Remittance Amount, and Transaction Date.
- **Strict Fixed Table Layout:** CSS `table-layout: fixed` ensures crisp column alignment across desktop and mobile viewports.
- **Branch Filtering:** Filter agent risk metrics across regional branch offices (`Accra`, `Kumasi`, `Tamale`, `Takoradi`, `Cape Coast`).

### 3. Dual-Factor Authentication & SMS OTP Engine
- **JWT Bearer Auth:** Secure registration and login backed by bcrypt password hashing and database-backed session validation.
- **Africa's Talking SMS OTP Verification:** Interactive SMS dialog (`SmsOtpDialog.js`) sends real-time 6-digit OTPs to mobile devices for identity verification before sensitive operations.

### 4. Dograh AI Outbound Voice Telephony Automation
- **Conversational Payment Reminders:** On-demand and scheduled outbound voice calls targeting agents with overdue remittances.
- **Dograh Workflow 9611 & Vonage Telephony 963:** Executes outbound calls using Dograh's AI conversational engine.
- **Automated Retry Scheduler:** APScheduler automatically retries un-answered calls up to 3 times spaced 2 hours apart.
- **Full Call Diagnostic Logging:** Outbound call outcomes and exact error tracebacks (e.g. Vonage account tier / phone number requirements) are stored in `public.voice_call_logs`.

### 5. Mobile Responsive Design
- Touch-optimized submit buttons (`touch-action: manipulation`) and responsive MUI card containers tailored for mobile viewports (375px+).

---

## 🚀 How to Run the App Locally

### Prerequisites
- Node.js (v18+) & npm
- Python (v3.10+)
- Supabase PostgreSQL account / database URL

### 1. Clone & Set Up Backend
```bash
cd micro-insurance-fraud-system
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Configure Environment (.env)
cp .env.example backend/.env
```
Ensure `backend/.env` contains your Supabase PostgreSQL connection string:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xvykfctqxsnttiibxvyu.supabase.co:5432/postgres
SECRET_KEY=your_secret_key_here
DOGRAH_API_KEY=your_dograh_api_key
DOGRAH_API_URL=https://api.dograh.com
DOGRAH_WORKFLOW_ID=9611
DOGRAH_TELEPHONY_CONFIG_ID=963
AT_API_KEY=your_africastalking_key
AT_USERNAME=your_africastalking_username
```

Start the FastAPI backend server:
```bash
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
Backend API interactive documentation available at: `http://localhost:8000/docs`

### 2. Set Up & Run Frontend
```bash
cd material-dashboard-react
npm install

# Configure Frontend Environment (.env)
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# Start Frontend Dev Server
npm run dev
# or: npm start
```
Frontend application opens at: `http://localhost:3000`

---

## 🌐 Live Production Deployments

- **Frontend (Render Static Site):** `https://insurance-fraud-4t3m.onrender.com`
- **Backend (Render Web Service):** `https://investment-project-3.onrender.com`
- **Database (Supabase PostgreSQL):** `db.xvykfctqxsnttiibxvyu.supabase.co:5432`
- **Source Code Repository:** `https://github.com/JoycelynAllan/insurance_fraud.git`
