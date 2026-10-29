import datetime
import json
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database.session import get_db
from backend.app.models.entities import (
    EmailEvent, EmailAnalysis, LoginEvent, LoginAnalysis,
    Incident, ResponseAction, AuditLog
)
from backend.app.core.config import settings

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_emails = db.query(EmailEvent).count()
    phishing_count = db.query(EmailAnalysis).filter(EmailAnalysis.predicted_class == "phishing").count()
    
    total_logins = db.query(LoginEvent).count()
    suspicious_logins = db.query(LoginAnalysis).filter(LoginAnalysis.is_suspicious == True).count()
    
    total_incidents = db.query(Incident).count()
    open_incidents = db.query(Incident).filter(Incident.status.in_(["New", "Investigating"])).count()
    high_risk_incidents = db.query(Incident).filter(Incident.severity.in_(["high", "critical"])).count()
    resolved_incidents = db.query(Incident).filter(Incident.status.in_(["Resolved", "Contained"])).count()
    
    phish_ratio = round((phishing_count / total_emails * 100), 1) if total_emails > 0 else 0.0
    
    return {
        "total_emails_analyzed": total_emails,
        "phishing_emails_detected": phishing_count,
        "phishing_ratio_percent": phish_ratio,
        "total_logins_monitored": total_logins,
        "suspicious_logins_detected": suspicious_logins,
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "high_risk_incidents": high_risk_incidents,
        "resolved_incidents": resolved_incidents,
        "demo_mode": settings.DEMO_MODE,
        "model_statuses": {
            "email_classifier": "Active (TF-IDF + Calibrated Classifier)",
            "login_anomaly_detector": "Active (Isolation Forest + Guardrails)",
            "correlation_engine": "Active (24-Hour Sliding Window)"
        }
    }

@router.get("/charts")
def get_dashboard_charts(db: Session = Depends(get_db)):
    # 1. Email Classification Breakdown
    email_phishing = db.query(EmailAnalysis).filter(EmailAnalysis.predicted_class == "phishing").count()
    email_safe = db.query(EmailAnalysis).filter(EmailAnalysis.predicted_class == "safe").count()
    email_chart = [
        {"name": "Phishing", "value": email_phishing, "fill": "#ef4444"},
        {"name": "Legitimate", "value": email_safe, "fill": "#10b981"}
    ]
    
    # 2. Login Severity Breakdown
    login_low = db.query(LoginAnalysis).filter(LoginAnalysis.severity == "low").count()
    login_med = db.query(LoginAnalysis).filter(LoginAnalysis.severity == "medium").count()
    login_high = db.query(LoginAnalysis).filter(LoginAnalysis.severity == "high").count()
    login_crit = db.query(LoginAnalysis).filter(LoginAnalysis.severity == "critical").count()
    login_chart = [
        {"name": "Low Risk", "count": login_low, "fill": "#10b981"},
        {"name": "Medium", "count": login_med, "fill": "#f59e0b"},
        {"name": "High", "count": login_high, "fill": "#f97316"},
        {"name": "Critical", "count": login_crit, "fill": "#ef4444"}
    ]
    
    # 3. Incident Severity Breakdown
    inc_low = db.query(Incident).filter(Incident.severity == "low").count()
    inc_med = db.query(Incident).filter(Incident.severity == "medium").count()
    inc_high = db.query(Incident).filter(Incident.severity == "high").count()
    inc_crit = db.query(Incident).filter(Incident.severity == "critical").count()
    incident_chart = [
        {"name": "Low", "count": inc_low, "fill": "#3b82f6"},
        {"name": "Medium", "count": inc_med, "fill": "#eab308"},
        {"name": "High", "count": inc_high, "fill": "#f97316"},
        {"name": "Critical", "count": inc_crit, "fill": "#dc2626"}
    ]
    
    # 4. Incident Status Breakdown
    statuses = ["New", "Investigating", "Contained", "Resolved", "False Positive"]
    status_chart = []
    for s in statuses:
        c = db.query(Incident).filter(Incident.status == s).count()
        status_chart.append({"status": s, "count": c})
        
    return {
        "email_classification": email_chart,
        "login_risk_distribution": login_chart,
        "incident_severity": incident_chart,
        "incident_status": status_chart
    }

@router.get("/activity")
def get_dashboard_activity(db: Session = Depends(get_db)):
    # Fetch latest critical/high events across emails, logins, and incidents
    recent_incidents = (
        db.query(Incident)
        .order_by(Incident.created_at.desc())
        .limit(5)
        .all()
    )
    
    recent_emails = (
        db.query(EmailEvent)
        .join(EmailAnalysis)
        .filter(EmailAnalysis.predicted_class == "phishing")
        .order_by(EmailEvent.timestamp.desc())
        .limit(5)
        .all()
    )
    
    recent_logins = (
        db.query(LoginEvent)
        .join(LoginAnalysis)
        .filter(LoginAnalysis.is_suspicious == True)
        .order_by(LoginEvent.timestamp.desc())
        .limit(5)
        .all()
    )
    
    activity = []
    for inc in recent_incidents:
        activity.append({
            "id": inc.incident_id,
            "type": "incident",
            "timestamp": inc.created_at.isoformat(),
            "title": f"Incident Created: {inc.title[:45]}...",
            "description": inc.evidence_summary or "Correlated multi-event incident",
            "severity": inc.severity,
            "user_id": inc.affected_user
        })
        
    for em in recent_emails:
        activity.append({
            "id": em.email_id,
            "type": "email",
            "timestamp": em.timestamp.isoformat(),
            "title": f"Phishing Email: {em.email_subject[:40]}...",
            "description": f"From {em.sender_name} ({em.sender_domain})",
            "severity": em.analysis.severity if em.analysis else "high",
            "user_id": em.user_id
        })
        
    for lg in recent_logins:
        activity.append({
            "id": lg.event_id,
            "type": "login",
            "timestamp": lg.timestamp.isoformat(),
            "title": f"Suspicious Sign-in from {lg.city}, {lg.country}",
            "description": f"IP: {lg.ip_address} | Impossible travel: {lg.impossible_travel}",
            "severity": lg.analysis.severity if lg.analysis else "high",
            "user_id": lg.user_id
        })
        
    # Sort unified activity by timestamp descending
    activity.sort(key=lambda x: x["timestamp"], reverse=True)
    return activity[:15]
