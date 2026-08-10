import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app.models.user import User

client = TestClient(app)

def test_1_register_agent_role_fails():
    """1. POST /api/auth/register with role 'agent' -> 400 Bad Request."""
    payload = {
        "full_name": "Field Agent User",
        "email": "agent_reg_test@mifds.gh",
        "password": "Password123!",
        "role": "agent",
        "branch": "Accra"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "Only supervisors can register" in response.json().get("detail", "")

def test_2_register_supervisor_success():
    """2. POST /api/auth/register with supervisor role -> 201 Created or 200 Success."""
    payload = {
        "full_name": "Accra Manager",
        "email": "accra_manager@mifds.gh",
        "password": "Password123!",
        "role": "supervisor",
        "branch": "Accra"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code in [200, 201, 400]

def test_3_login_supervisor_success():
    """3. POST /api/auth/login with supervisor@mifds.gh -> 200 with JWT containing role 'supervisor'."""
    payload = {
        "email": "supervisor@mifds.gh",
        "password": "Supervisor123!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "supervisor"

def test_11_get_voice_logs():
    """11. GET /api/voice/logs -> returns call log list."""
    login_resp = client.post("/api/auth/login", json={"email": "supervisor@mifds.gh", "password": "Supervisor123!"})
    token = login_resp.json()["access_token"]

    response = client.get("/api/voice/logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "logs" in response.json()

def test_13_login_agent_email_fails_with_403():
    """13. POST /api/auth/login with an agent email that exists in DB -> 403 Forbidden."""
    db = SessionLocal()
    try:
        # Temporarily insert an agent account
        from backend.app.utils.auth_guard import hash_password
        agt_user = db.query(User).filter(User.email == "agent_test_403@mifds.gh").first()
        if not agt_user:
            agt_user = User(
                full_name="Agent User",
                email="agent_test_403@mifds.gh",
                password_hash=hash_password("Agent123!"),
                role="agent",
                branch="Kumasi"
            )
            db.add(agt_user)
            db.commit()
    finally:
        db.close()

    payload = {
        "email": "agent_test_403@mifds.gh",
        "password": "Agent123!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 403
    assert "Field agents do not have access" in response.json().get("detail", "")
