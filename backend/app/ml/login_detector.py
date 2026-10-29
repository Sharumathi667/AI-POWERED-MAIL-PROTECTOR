import os
import joblib
import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from backend.app.core.config import settings

FEATURE_COLS = [
    "login_hour",
    "day_of_week",
    "failed_attempts",
    "is_new_device",
    "is_new_location",
    "distance_from_usual_location_km",
    "minutes_since_previous_login",
    "login_success",
    "impossible_travel"
]

class LoginDetectorService:
    def __init__(self):
        self.artifact = None
        self.scaler = None
        self.model = None
        self.calib = None
        self.load_model()
        
    def load_model(self):
        if os.path.exists(settings.LOGIN_MODEL_PATH):
            try:
                self.artifact = joblib.load(settings.LOGIN_MODEL_PATH)
                self.scaler = self.artifact.get("scaler")
                self.model = self.artifact.get("model")
                self.calib = self.artifact.get("score_calibration", {"min_val": -0.2, "max_val": 0.2})
                print(f"[LoginDetectorService] Successfully loaded login model from {settings.LOGIN_MODEL_PATH}")
            except Exception as e:
                print(f"[LoginDetectorService] Error loading login model: {e}")
        else:
            print(f"[LoginDetectorService] Model artifact not found at {settings.LOGIN_MODEL_PATH}")
            
    def analyze_login(self, login_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs Isolation Forest anomaly detection combined with security heuristics.
        Returns:
            anomaly_score, risk_score, severity, is_suspicious, reasons,
            recommended_actions, component breakdown
        """
        timestamp_raw = login_data.get("timestamp")
        if isinstance(timestamp_raw, str):
            try:
                dt = pd.to_datetime(timestamp_raw)
            except Exception:
                dt = datetime.datetime.utcnow()
        elif isinstance(timestamp_raw, datetime.datetime):
            dt = timestamp_raw
        else:
            dt = datetime.datetime.utcnow()
            
        hour = dt.hour
        day_of_week = dt.weekday()
        failed_attempts = int(login_data.get("failed_attempts") or 0)
        is_new_device = int(login_data.get("is_new_device") or 0)
        is_new_location = int(login_data.get("is_new_location") or 0)
        dist_km = float(login_data.get("distance_from_usual_location_km") or 0.0)
        mins_prev = float(login_data.get("minutes_since_previous_login") or 60.0)
        login_success = int(login_data.get("login_success") if login_data.get("login_success") is not None else 1)
        impossible_travel = int(login_data.get("impossible_travel") or 0)
        browser = str(login_data.get("browser") or "")
        country = str(login_data.get("country") or "")
        city = str(login_data.get("city") or "")
        ip = str(login_data.get("ip_address") or "")
        
        # 1. Isolation Forest Model Score
        anomaly_score = 15.0
        is_model_anomaly = False
        
        if self.model is not None and self.scaler is not None:
            try:
                row_features = pd.DataFrame([{
                    "login_hour": hour,
                    "day_of_week": day_of_week,
                    "failed_attempts": failed_attempts,
                    "is_new_device": is_new_device,
                    "is_new_location": is_new_location,
                    "distance_from_usual_location_km": dist_km,
                    "minutes_since_previous_login": mins_prev,
                    "login_success": login_success,
                    "impossible_travel": impossible_travel
                }])[FEATURE_COLS]
                
                scaled = self.scaler.transform(row_features)
                pred_label = self.model.predict(scaled)[0]
                is_model_anomaly = (pred_label == -1)
                
                raw_decision = self.model.decision_function(scaled)[0]
                min_v = self.calib.get("min_val", -0.2)
                max_v = self.calib.get("max_val", 0.2)
                clipped = np.clip(raw_decision, min_v, max_v)
                norm = 1.0 - ((clipped - min_v) / (max_v - min_v + 1e-9))
                anomaly_score = round(float(norm * 100), 1)
            except Exception as e:
                print(f"[LoginDetectorService] Inference error: {e}")
                
        # 2. Heuristic Signals & Explanations
        reasons: List[str] = []
        recommended_actions: List[str] = []
        
        # --- Location Risk (0 - 100) ---
        location_risk = 0.0
        if impossible_travel == 1:
            location_risk += 85
            reasons.append(f"Impossible travel violation: distance of {dist_km:,.0f} km reached within {mins_prev:.0f} minutes")
        elif dist_km > 2000:
            location_risk += 60
            reasons.append(f"Sign-in location is {dist_km:,.0f} km away from established primary campus baseline ({city}, {country})")
        elif is_new_location == 1:
            location_risk += 35
            reasons.append(f"First-time authentication recorded from {city}, {country}")
            
        location_risk = min(100.0, location_risk)
        
        # --- Device Risk (0 - 100) ---
        device_risk = 0.0
        if is_new_device == 1:
            device_risk += 45
            reasons.append("Authentication from a newly observed device identifier")
            
        if "tor" in browser.lower() or "headless" in browser.lower() or "python" in browser.lower() or "curl" in browser.lower():
            device_risk += 50
            reasons.append(f"Anonymizing proxy, Tor browser, or automated script detected ({browser})")
            
        device_risk = min(100.0, device_risk)
        
        # --- Authentication Risk (0 - 100) ---
        auth_risk = 0.0
        if failed_attempts >= 5:
            auth_risk += 75
            reasons.append(f"High-frequency failed attempt burst ({failed_attempts} failed attempts preceding current event)")
        elif failed_attempts >= 2:
            auth_risk += 40
            reasons.append(f"{failed_attempts} prior failed attempts logged before authentication")
            
        if login_success == 0:
            auth_risk += 25
            reasons.append("Login authentication attempt was rejected/failed")
        elif failed_attempts >= 3 and login_success == 1:
            auth_risk += 35
            reasons.append("Brute-force credential stuffing signature: successful login achieved after repeated failed attempts")
            
        auth_risk = min(100.0, auth_risk)
        
        # --- Behavior Risk (0 - 100) ---
        behavior_risk = 0.0
        if 1 <= hour <= 4:
            behavior_risk += 40
            reasons.append(f"Authentication occurred during anomalous low-activity hours ({hour:02d}:00 local time)")
        if mins_prev < 10 and dist_km > 50:
            behavior_risk += 35
            reasons.append("Sudden rapid re-authentication velocity across divergent network segments")
            
        behavior_risk = min(100.0, behavior_risk)
        
        # --- Overall Weighted Login Risk Score ---
        # Formula: 0.35 * Location + 0.30 * Device + 0.20 * Auth + 0.15 * Behavior
        heuristic_risk = (
            settings.LOGIN_WEIGHT_LOCATION * location_risk +
            settings.LOGIN_WEIGHT_DEVICE * device_risk +
            settings.LOGIN_WEIGHT_AUTHENTICATION * auth_risk +
            settings.LOGIN_WEIGHT_BEHAVIOR * behavior_risk
        )
        
        # Reconcile heuristic risk with ML Anomaly score:
        # If impossible travel or high failed attempts, enforce high risk
        if impossible_travel == 1 or failed_attempts >= 5:
            final_risk = max(heuristic_risk, anomaly_score, 82.0)
        else:
            final_risk = 0.60 * heuristic_risk + 0.40 * anomaly_score
            
        final_risk = round(min(100.0, max(0.0, final_risk)), 1)
        
        is_suspicious = (final_risk >= 60.0) or (impossible_travel == 1) or is_model_anomaly
        
        # Severity calculation
        if final_risk <= settings.SEVERITY_LOW_MAX:
            severity = "low"
        elif final_risk <= settings.SEVERITY_MED_MAX:
            severity = "medium"
        elif final_risk <= settings.SEVERITY_HIGH_MAX:
            severity = "high"
        else:
            severity = "critical"
            
        # Tailored Recommended Actions
        if severity in ("high", "critical") or impossible_travel == 1:
            recommended_actions.append("Prompt account owner with an out-of-band verification challenge")
            recommended_actions.append("Revoke all active SSO session tokens for this user")
            recommended_actions.append("Initiate mandatory password reset procedure")
            recommended_actions.append("Correlate with recent suspicious email alerts for this account")
        elif severity == "medium":
            recommended_actions.append("Require Multi-Factor Authentication (MFA) step-up confirmation")
            recommended_actions.append("Notify user of unfamiliar sign-in activity via registered mobile device")
        else:
            recommended_actions.append("Record successful authentication in routine telemetry baseline")
            
        if not reasons:
            reasons.append("Login occurred from recognized device and customary campus location during regular hours")
            
        return {
            "anomaly_score": anomaly_score,
            "risk_score": final_risk,
            "severity": severity,
            "is_suspicious": is_suspicious,
            "reasons": reasons,
            "recommended_actions": recommended_actions,
            "location_risk": round(location_risk, 1),
            "device_risk": round(device_risk, 1),
            "auth_risk": round(auth_risk, 1),
            "behavior_risk": round(behavior_risk, 1),
            "model_version": "login-v1.0"
        }

login_detector = LoginDetectorService()
