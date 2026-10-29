"""
Database Seeding Script
Populates SQLite database with users, synthetic email events, login telemetry,
real ML model analysis outputs, and automatically generates correlated incidents.
"""

import os
import sys
import json
import datetime
import pandas as pd
from sqlalchemy.orm import Session

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

from backend.app.database.session import SessionLocal, engine, Base
from backend.app.models.entities import (
    User, EmailEvent, EmailAnalysis, LoginEvent, LoginAnalysis,
    Incident, AuditLog, SystemSetting
)
from backend.app.ml.email_classifier import email_classifier
from backend.app.ml.login_detector import login_detector
from backend.app.services.correlation_engine import correlation_engine

def seed():
    print("=" * 60)
    print("SEEDING INVESTIGATION DATABASE")
    print("=" * 60)
    
    # 1. Ensure tables created
    Base.metadata.drop_all(bind=engine) # Fresh start for demo consistency
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized.")
    
    db: Session = SessionLocal()
    
    try:
        # 2. Seed Default Application Users
        users = [
            User(username="admin", email="admin@campus.edu", full_name="Chief Information Security Officer", role="admin"),
            User(username="analyst", email="analyst@campus.edu", full_name="SOC Lead Analyst", role="analyst"),
            User(username="demo", email="demo@campus.edu", full_name="Guest Evaluator", role="demo")
        ]
        db.add_all(users)
        db.commit()
        print("Default users seeded.")
        
        # 3. Load synthetic emails
        email_csv = os.path.join(PROJECT_ROOT, "backend", "data", "raw", "synthetic_emails.csv")
        if not os.path.exists(email_csv):
            email_csv = os.path.join(PROJECT_ROOT, "data", "raw", "synthetic_emails.csv")
        if not os.path.exists(email_csv):
            print(f"Error: synthetic_emails.csv not found at {email_csv}. Run generate_synthetic_data.py first.")
            return
            
        email_df = pd.read_csv(email_csv)
        # Select first 1,500 records to keep DB fast and responsive for demo
        sample_emails = email_df.head(1500)
        print(f"Processing and classifying {len(sample_emails)} emails with ML model...")
        
        email_events = []
        email_analyses = []
        
        for _, row in sample_emails.iterrows():
            ts = pd.to_datetime(row["timestamp"])
            ee = EmailEvent(
                email_id=row["email_id"],
                user_id=row["user_id"],
                timestamp=ts,
                sender_name=row["sender_name"],
                sender_email=row["sender_email"],
                sender_domain=row["sender_domain"],
                reply_to=row["reply_to"],
                email_subject=row["email_subject"],
                email_body=row["email_body"],
                urls=str(row["urls"]) if pd.notnull(row["urls"]) else "",
                link_count=int(row["link_count"]),
                has_attachment=int(row["has_attachment"]),
                attachment_type=str(row["attachment_type"]),
                spf_result=str(row["spf_result"]),
                dkim_result=str(row["dkim_result"]),
                dmarc_result=str(row["dmarc_result"]),
                display_name_mismatch=int(row["display_name_mismatch"]),
                domain_age_category=str(row["domain_age_category"]),
                label=str(row["label"]),
                data_source="synthetic"
            )
            email_events.append(ee)
            
            # Run ML & Rule Engine
            analysis = email_classifier.analyze_email(row.to_dict())
            ea = EmailAnalysis(
                email_id=row["email_id"],
                predicted_class=analysis["predicted_class"],
                phishing_probability=analysis["phishing_probability"],
                risk_score=analysis["risk_score"],
                severity=analysis["severity"],
                reasons=json.dumps(analysis["reasons"]),
                recommended_actions=json.dumps(analysis["recommended_actions"]),
                content_risk=analysis["content_risk"],
                url_risk=analysis["url_risk"],
                sender_risk=analysis["sender_risk"],
                model_version=analysis["model_version"]
            )
            email_analyses.append(ea)
            
        db.bulk_save_objects(email_events)
        db.bulk_save_objects(email_analyses)
        db.commit()
        print(f"Seeded {len(email_events)} emails with real ML predictions.")
        
        # 4. Load synthetic logins
        login_csv = os.path.join(PROJECT_ROOT, "backend", "data", "raw", "synthetic_login_events.csv")
        if not os.path.exists(login_csv):
            login_csv = os.path.join(PROJECT_ROOT, "data", "raw", "synthetic_login_events.csv")
        if not os.path.exists(login_csv):
            print(f"Error: synthetic_login_events.csv not found at {login_csv}.")
            return
            
        login_df = pd.read_csv(login_csv)
        sample_logins = login_df.head(3000)
        print(f"Processing and evaluating {len(sample_logins)} login events with Anomaly Detector...")
        
        login_events = []
        login_analyses = []
        
        for _, row in sample_logins.iterrows():
            ts = pd.to_datetime(row["timestamp"])
            le = LoginEvent(
                event_id=row["event_id"],
                user_id=row["user_id"],
                timestamp=ts,
                ip_address=row["ip_address"],
                country=row["country"],
                city=row["city"],
                device_id=row["device_id"],
                device_type=row["device_type"],
                browser=row["browser"],
                operating_system=row["operating_system"],
                login_success=int(row["login_success"]),
                failed_attempts=int(row["failed_attempts"]),
                is_new_device=int(row["is_new_device"]),
                is_new_location=int(row["is_new_location"]),
                distance_from_usual_location_km=float(row["distance_from_usual_location_km"]),
                minutes_since_previous_login=float(row["minutes_since_previous_login"]),
                impossible_travel=int(row["impossible_travel"]),
                label=str(row["label"]),
                data_source="synthetic"
            )
            login_events.append(le)
            
            # Run Isolation Forest & Rule Guardrails
            analysis = login_detector.analyze_login(row.to_dict())
            la = LoginAnalysis(
                event_id=row["event_id"],
                anomaly_score=analysis["anomaly_score"],
                risk_score=analysis["risk_score"],
                severity=analysis["severity"],
                is_suspicious=analysis["is_suspicious"],
                reasons=json.dumps(analysis["reasons"]),
                recommended_actions=json.dumps(analysis["recommended_actions"]),
                location_risk=analysis["location_risk"],
                device_risk=analysis["device_risk"],
                auth_risk=analysis["auth_risk"],
                behavior_risk=analysis["behavior_risk"],
                model_version=analysis["model_version"]
            )
            login_analyses.append(la)
            
        db.bulk_save_objects(login_events)
        db.bulk_save_objects(login_analyses)
        db.commit()
        print(f"Seeded {len(login_events)} logins with real anomaly scores.")
        
        # 5. Run Correlation Engine to discover and link incidents
        print("Running Incident Correlation Engine across all campus accounts...")
        all_users = sample_emails["user_id"].unique()
        total_incidents = 0
        for uid in all_users:
            incidents = correlation_engine.correlate_user_events(db, uid)
            total_incidents += len(incidents)
            
        print(f"Successfully generated {total_incidents} correlated security incidents with evidence chains!")
        
        # 6. Seed initial audit log
        audit = AuditLog(
            action="DATABASE_INITIALIZED_AND_SEEDED",
            target_type="system",
            target_id="investigation_db",
            actor="System Setup Routine",
            details=json.dumps({
                "emails_seeded": len(email_events),
                "logins_seeded": len(login_events),
                "incidents_created": total_incidents,
                "is_demo_mode": True
            }),
            is_simulated=True
        )
        db.add(audit)
        db.commit()
        print("Initial audit log entry recorded.")
        print("\nDatabase seeding completed successfully!")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed()
