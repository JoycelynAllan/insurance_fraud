# Micro-Insurance Fraud System

This repository serves as the master project scaffold linking all components of our AI-enabled micro-insurance fraud detection platform.

## Project Structure

The project integrates machine learning model training, a Flask-based inference backend, a responsive React dashboard, and a voice agent platform:

```
micro-insurance-fraud-system/
├── backend/          # ML backend (Flask + Isolation Forest & fraud models)
├── frontend/         # UI Dashboard (React-based admin panel)
├── voice/            # Voice agent interaction platform
├── data/             # Dataset storage
│   └── synthetic/    # Synthetic transaction data for testing and local runs
├── docker-compose.yml
└── README.md
```

---

## Component Origins (Cloned Repositories)

The system integrates three open-source codebases cloned at the root level of the workspace:

1. **`AI-Enabled-Fraud-Detection/`** — Flask-based API service featuring Isolation Forest anomaly detection. (MIT License)
2. **`material-dashboard-react/`** — Material Dashboard React template used for the system analytics dashboard UI. (MIT License)
3. **`dograh/`** — Voice agent and conversational system used for interactive voice fraud response. (BSD-2-Clause License)

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
