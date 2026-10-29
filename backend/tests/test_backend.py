import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project_id"] == "PS 1.3"

def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_emails_analyzed"] > 0
    assert data["phishing_emails_detected"] > 0
    assert data["total_logins_monitored"] > 0
    assert data["total_incidents"] > 0

def test_dashboard_charts():
    response = client.get("/api/dashboard/charts")
    assert response.status_code == 200
    data = response.json()
    assert "email_classification" in data
    assert "login_risk_distribution" in data
    assert "incident_severity" in data

def test_dashboard_activity():
    response = client.get("/api/dashboard/activity")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_list_emails():
    response = client.get("/api/emails?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 10
    first = data["items"][0]
    assert "email_id" in first
    assert "analysis" in first
    assert first["analysis"]["risk_score"] is not None

def test_get_email_details():
    # First get an email_id
    list_res = client.get("/api/emails?limit=1")
    email_id = list_res.json()["items"][0]["email_id"]
    
    res = client.get(f"/api/emails/{email_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["email_id"] == email_id
    assert "related_logins" in data

def test_email_custom_analyze():
    payload = {
        "user_id": "USER-1005",
        "sender_name": "Suspicious Admin",
        "sender_email": "security@fake-campus-alert.xyz",
        "email_subject": "Urgent: Reset campus pass now",
        "email_body": "Your account will be suspended. Click here: https://fake-campus-alert.xyz/verify",
        "urls": "https://fake-campus-alert.xyz/verify",
        "link_count": 1,
        "spf_result": "fail"
    }
    response = client.post("/api/emails/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["analysis"]["predicted_class"] == "phishing"
    assert data["analysis"]["risk_score"] > 60

def test_list_logins():
    response = client.get("/api/logins?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 10
    first = data["items"][0]
    assert "event_id" in first
    assert first["analysis"]["anomaly_score"] is not None

def test_list_incidents():
    response = client.get("/api/incidents")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0

def test_incident_details_and_timeline():
    list_res = client.get("/api/incidents")
    inc_id = list_res.json()["items"][0]["incident_id"]
    
    # Detail
    res = client.get(f"/api/incidents/{inc_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["incident_id"] == inc_id
    assert len(data["evidence_items"]) > 0
    
    # Timeline
    tl_res = client.get(f"/api/incidents/{inc_id}/timeline")
    assert tl_res.status_code == 200
    assert len(tl_res.json()) > 0

def test_response_action_workflow():
    # List actions
    actions_res = client.get("/api/actions")
    assert actions_res.status_code == 200
    actions = actions_res.json()
    assert len(actions) > 0
    
    target_action = actions[0]
    action_id = target_action["action_id"]
    
    # Approve action
    app_res = client.post(f"/api/actions/{action_id}/approve", json={
        "analyst_name": "Test SOC Lead",
        "notes": "Automated test validation approval"
    })
    assert app_res.status_code == 200
    app_data = app_res.json()
    assert app_data["status"] == "executed"
    assert "SIMULATED ACTION EXECUTED" in app_data["execution_result"]
    
    # Check audit log contains the entry
    audit_res = client.get(f"/api/audit-logs?action=RESPONSE_ACTION_APPROVED_AND_EXECUTED")
    assert audit_res.status_code == 200
    logs = audit_res.json()["items"]
    assert any(l["target_id"] == action_id for l in logs)

def test_models_and_metrics_endpoints():
    res = client.get("/api/models")
    assert res.status_code == 200
    assert len(res.json()) >= 3
    
    metrics_res = client.get("/api/models/metrics")
    assert metrics_res.status_code == 200
    data = metrics_res.json()
    assert "email_model" in data
    assert "login_model" in data

def test_auth_and_session_workflow():
    # 1. Check auth config
    config_res = client.get("/api/auth/config")
    assert config_res.status_code == 200
    assert "is_google_configured" in config_res.json()

    # 2. Check unauthenticated me
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["is_authenticated"] is False

    # 3. Perform Demo SOC Analyst Login
    login_res = client.post("/api/auth/demo-login", json={"role": "analyst"})
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["is_authenticated"] is True
    assert login_data["user"]["role"] == "analyst"

    # 4. Check authenticated me (cookie preserved in TestClient session)
    auth_me = client.get("/api/auth/me")
    assert auth_me.status_code == 200
    assert auth_me.json()["is_authenticated"] is True
    assert "analyst" in auth_me.json()["user"]["email"]

    # 5. Check integrations status
    int_res = client.get("/api/integrations/status")
    assert int_res.status_code == 200
    assert "gmail" in int_res.json()

    # 6. Logout
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["is_authenticated"] is False

