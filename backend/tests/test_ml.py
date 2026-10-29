import os
import json
import pytest
from backend.app.ml.email_classifier import email_classifier
from backend.app.ml.login_detector import login_detector
from backend.app.services.risk_engine import risk_engine
from backend.app.core.config import settings

def test_email_model_artifact_and_metrics():
    assert os.path.exists(settings.EMAIL_MODEL_PATH), "Email model artifact missing"
    assert os.path.exists(settings.EMAIL_METRICS_PATH), "Email metrics JSON missing"
    
    with open(settings.EMAIL_METRICS_PATH, "r") as f:
        metrics = json.load(f)
        
    assert "metrics" in metrics
    assert metrics["metrics"]["accuracy"] > 0.85
    assert metrics["metrics"]["f1_score"] > 0.85
    assert "confusion_matrix" in metrics["metrics"]

def test_login_model_artifact_and_metrics():
    assert os.path.exists(settings.LOGIN_MODEL_PATH), "Login model artifact missing"
    assert os.path.exists(settings.LOGIN_METRICS_PATH), "Login metrics JSON missing"
    
    with open(settings.LOGIN_METRICS_PATH, "r") as f:
        metrics = json.load(f)
        
    assert "metrics" in metrics
    assert metrics["metrics"]["accuracy"] > 0.85
    assert metrics["metrics"]["f1_score"] > 0.80

def test_email_classifier_inference_bounds_and_explanations():
    sample_phish = {
        "email_subject": "CRITICAL: Urgent Password Reset Required",
        "email_body": "Your campus credentials expire in 2 hours. Reset immediately at https://campus-auth-security.xyz/login-auth",
        "sender_name": "Campus IT Support",
        "sender_email": "support@campus-auth-security.xyz",
        "sender_domain": "campus-auth-security.xyz",
        "reply_to": "service@temp-mail.com",
        "urls": "https://campus-auth-security.xyz/login-auth",
        "link_count": 1,
        "has_attachment": 0,
        "attachment_type": "none",
        "spf_result": "fail",
        "dkim_result": "fail",
        "dmarc_result": "fail",
        "display_name_mismatch": 1,
        "domain_age_category": "new_<30d"
    }
    
    res = email_classifier.analyze_email(sample_phish)
    assert 0.0 <= res["risk_score"] <= 100.0
    assert 0.0 <= res["phishing_probability"] <= 1.0
    assert res["predicted_class"] == "phishing"
    assert res["severity"] in ["high", "critical"]
    assert len(res["reasons"]) > 0
    assert len(res["recommended_actions"]) > 0

def test_login_detector_impossible_travel_and_rules():
    sample_anomaly = {
        "timestamp": "2026-10-15 14:30:00",
        "ip_address": "203.0.113.88",
        "country": "Russia",
        "city": "Moscow",
        "device_id": "DEV-ROGUE-999",
        "device_type": "desktop",
        "browser": "Unknown/TorBrowser",
        "operating_system": "Linux",
        "login_success": 1,
        "failed_attempts": 6,
        "is_new_device": 1,
        "is_new_location": 1,
        "distance_from_usual_location_km": 7200.0,
        "minutes_since_previous_login": 25.0,
        "impossible_travel": 1
    }
    
    res = login_detector.analyze_login(sample_anomaly)
    assert 0.0 <= res["risk_score"] <= 100.0
    assert 0.0 <= res["anomaly_score"] <= 100.0
    assert res["is_suspicious"] is True
    assert res["severity"] in ["high", "critical"]
    assert any("impossible travel" in r.lower() for r in res["reasons"])

def test_risk_engine_correlation_bounds():
    incident_res = risk_engine.calculate_incident_risk(
        email_risk=85.0,
        login_risk=90.0,
        time_delta_hours=1.5,
        has_credential_phish=True,
        is_compromised_login=True
    )
    assert 0.0 <= incident_res["risk_score"] <= 100.0
    assert incident_res["correlation_bonus"] <= settings.MAX_CORRELATION_BONUS
    assert incident_res["severity"] == "critical"
    assert len(incident_res["bonus_factors"]) > 0
