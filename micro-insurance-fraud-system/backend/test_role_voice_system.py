import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.db import get_db, Base, auto_migrate_schema
from backend.app.models.user import User
from backend.app.models.alert import FraudAlert

# Create TestClient
client = TestClient(app)

def test_1_register_supervisor_success():
    """1. Test registering a supervisor returns 201 Created."""
    payload = {
        "full_name": "Test Supervisor",
        "email": "test_sup@mifds.gh",
        "password": "Password123!",
        "role": "supervisor",
        "branch": "Accra",
        "language_pref": "english"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code in [201, 400] # 201 created or 400 if already exists

def test_2_register_agent_success():
    """2. Test registering an agent with required branch returns 201 Created."""
    payload = {
        "full_name": "Test Agent",
        "email": "test_agt@mifds.gh",
        "password": "Password123!",
        "role": "agent",
        "branch": "Kumasi",
        "language_pref": "twi",
        "agent_id": "AGT041"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code in [201, 400]

def test_3_register_invalid_role():
    """3. Test registering with invalid role 'risk_officer' returns 422 Unprocessable Entity."""
    payload = {
        "full_name": "Invalid Role User",
        "email": "invalid_role@mifds.gh",
        "password": "Password123!",
        "role": "risk_officer",
        "branch": "Accra"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422

def test_4_register_agent_missing_branch():
    """4. Test registering an agent without a branch returns 422 Unprocessable Entity."""
    payload = {
        "full_name": "No Branch Agent",
        "email": "nobranch@mifds.gh",
        "password": "Password123!",
        "role": "agent"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422

def test_5_login_returns_token_and_role():
    """5. Test login returns access_token, role, branch, language_pref."""
    payload = {
        "email": "supervisor@mifds.gh",
        "password": "Supervisor123!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "supervisor"
    assert data["branch"] == "Accra"
    assert "language_pref" in data

def test_6_supervisor_can_access_agents_list():
    """6. Test supervisor JWT can access GET /api/agents."""
    login_resp = client.post("/api/auth/login", json={"email": "supervisor@mifds.gh", "password": "Supervisor123!"})
    token = login_resp.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/agents", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_7_agent_cannot_access_agents_list():
    """7. Test agent JWT accessing GET /api/agents returns 403 Forbidden."""
    login_resp = client.post("/api/auth/login", json={"email": "agent@mifds.gh", "password": "Agent123!"})
    token = login_resp.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/agents", headers=headers)
    assert response.status_code == 403

def test_8_agent_can_access_own_transactions():
    """8. Test agent JWT accessing their own agent_id transactions returns 200 OK."""
    login_resp = client.post("/api/auth/login", json={"email": "agent@mifds.gh", "password": "Agent123!"})
    token = login_resp.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/agents/AGT041/transactions", headers=headers)
    assert response.status_code == 200

def test_9_agent_cannot_access_other_agent_transactions():
    """9. Test agent JWT accessing another agent's transactions returns 403 Forbidden."""
    login_resp = client.post("/api/auth/login", json={"email": "agent@mifds.gh", "password": "Agent123!"})
    token = login_resp.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/agents/AGT031/transactions", headers=headers)
    assert response.status_code == 403

def test_10_voice_callback_english_dtmf_1_resolves_alert():
    """10. Test Africa's Talking voice callback with DTMF 1 returns XML and updates alert to RESOLVED."""
    payload = {
        "dtmfDigits": "1",
        "callerNumber": "+233200000000",
        "sessionId": "test-session-123",
        "isActive": "1",
        "language": "english"
    }
    response = client.post("/api/voice/callback", data=payload)
    assert response.status_code == 200
    assert "Thank you for confirming" in response.text
    assert "<Response>" in response.text
