import pytest
from fastapi.testclient import TestClient
from apps.api.app.main import app
from apps.api.app.core.database import get_db

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert data["redis"] == "ok"


def test_auth_login_success():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "finance@acme.test", "password": "DemoPassword123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "finance@acme.test"
    assert data["user"]["role"] == "FINANCE_MANAGER"


def test_auth_login_invalid_password():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "finance@acme.test", "password": "WrongPassword!"}
    )
    assert response.status_code == 401


def test_authenticated_dashboard_and_command():
    # 1. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "finance@acme.test", "password": "DemoPassword123!"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Dashboard
    dash_res = client.get("/api/v1/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "metrics" in dash_data
    assert "automation_rate" in dash_data["metrics"]

    # 3. Agents Fleet
    agents_res = client.get("/api/v1/agents", headers=headers)
    assert agents_res.status_code == 200
    assert len(agents_res.json()["agents"]) >= 10

    # 4. Command Center
    cmd_res = client.post(
        "/api/v1/command",
        headers=headers,
        json={"query": "Show invoices above 1 lakh"}
    )
    assert cmd_res.status_code == 200
    cmd_data = cmd_res.json()
    assert cmd_data["intent"] == "FILTER_HIGH_VALUE_INVOICES"


def test_test_lab_scenarios_and_execution():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@acme.test", "password": "DemoPassword123!"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List scenarios
    sc_res = client.get("/api/v1/test-lab/scenarios", headers=headers)
    assert sc_res.status_code == 200
    assert len(sc_res.json()["scenarios"]) == 14

    # Run single scenario: Prompt Injection Defense
    run_res = client.post(
        "/api/v1/test-lab/run",
        headers=headers,
        json={"scenario_id": "SCENARIO-09"}
    )
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["passed"] == 1
    assert run_data["results"][0]["test_id"] == "SCENARIO-09"
    assert run_data["results"][0]["status"] == "PASSED"
    assert run_data["results"][0]["tool_blocked"] is True
