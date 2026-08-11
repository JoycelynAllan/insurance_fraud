# Micro-Insurance Fraud System

This repository serves as the master project scaffold linking all components of our AI-enabled micro-insurance fraud detection platform.

## Project Structure

The project integrates machine learning model training, a FastAPI inference backend, a responsive React dashboard, and Africa's Talking voice/SMS integration:

```
micro-insurance-fraud-system/
├── backend/          # ML backend (FastAPI + Isolation Forest & XGBoost fraud models)
├── frontend/         # UI Dashboard (React-based admin panel)
├── voice/            # Voice and SMS automation via Africa's Talking
├── data/             # Dataset storage
│   └── synthetic/    # Synthetic transaction data for testing and local runs
├── docker-compose.yml
└── README.md
```

---

## Component Origins (Cloned Repositories)

The system integrates open-source components cloned at the root level of the workspace:

1. **`AI-Enabled-Fraud-Detection/`** — Inference API service featuring Isolation Forest anomaly detection. (MIT License)
2. **`material-dashboard-react/`** — Material Dashboard React template used for the system analytics dashboard UI. (MIT License)

---

## Setup & Running

### 1. Prerequisites
Ensure you have the following installed:
* Docker and Docker Compose
* Git

### 2. Environment Setup
Clone or copy `.env.example` to `.env` in the root of the project:
```bash
cp .env.example .env
```
Fill in the credentials and endpoint URLs for the databases and external service APIs.

### 3. Spin up the infrastructure
Run the following command to boot up the database, cache, backend and frontend containers:
```bash
docker compose up --build
```
The services will be exposed at:
* **Backend API**: `http://localhost:8000`
* **Frontend UI Dashboard**: `http://localhost:3000`
* **PostgreSQL Database**: `localhost:5432`
* **Redis Cache**: `localhost:6379`
