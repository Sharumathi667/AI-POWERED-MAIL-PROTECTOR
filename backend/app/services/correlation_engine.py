import datetime
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.entities import (
    EmailEvent, EmailAnalysis, LoginEvent, LoginAnalysis,
    Incident, IncidentEvidence, ResponseAction, AuditLog
)
from backend.app.services.risk_engine import risk_engine

class CorrelationEngine:
    def correlate_user_events(self, db: Session, user_id: str) -> List[Incident]:
        """
        Scans a user's recent email events and login events within the correlation window.
        Identifies potential account compromise chains and links them into an Incident.
        """
        # Fetch user's emails with analysis
        emails = (
            db.query(EmailEvent)
            .join(EmailAnalysis)
            .filter(EmailEvent.user_id == user_id)
            .order_by(EmailEvent.timestamp.desc())
            .limit(10)
            .all()
        )
        
        # Fetch user's logins with analysis
        logins = (
            db.query(LoginEvent)
            .join(LoginAnalysis)
            .filter(LoginEvent.user_id == user_id)
            .order_by(LoginEvent.timestamp.desc())
            .limit(15)
            .all()
        )
        
        created_incidents = []
        
        for email in emails:
            e_analysis = email.analysis
            if not e_analysis or e_analysis.risk_score < 45.0:
                continue
                
            e_time = email.timestamp
            
            # Find matching logins occurring in window [e_time - 2h, e_time + 48h]
            matching_logins = []
            for login in logins:
                l_analysis = login.analysis
                if not l_analysis:
                    continue
                    
                time_diff_hours = (login.timestamp - e_time).total_seconds() / 3600.0
                
                # If login happened within 0 to 48 hours after phishing email
                if 0 <= time_diff_hours <= settings.CORRELATION_WINDOW_HOURS and (l_analysis.risk_score >= 45.0 or login.impossible_travel == 1):
                    matching_logins.append((login, time_diff_hours))
                    
            if not matching_logins:
                continue
                
            for login, delta_h in matching_logins:
                l_analysis = login.analysis
                
                # Check if an incident already associates this email and login
                existing_inc = (
                    db.query(Incident)
                    .join(IncidentEvidence)
                    .filter(
                        Incident.affected_user == user_id,
                        IncidentEvidence.event_id.in_([email.email_id, login.event_id])
                    )
                    .first()
                )
                
                if existing_inc:
                    continue
                    
                # Calculate Correlated Incident Risk
                has_cred = "password" in email.email_subject.lower() or "verify" in email.email_subject.lower() or "credential" in email.email_body.lower()
                is_comp = login.login_success == 1 and (login.is_new_device == 1 or login.is_new_location == 1)
                
                risk_res = risk_engine.calculate_incident_risk(
                    email_risk=e_analysis.risk_score,
                    login_risk=l_analysis.risk_score,
                    time_delta_hours=delta_h,
                    has_credential_phish=has_cred,
                    is_compromised_login=is_comp
                )
                
                incident_id = f"INC-{user_id.replace('USER-', '')}-{int(datetime.datetime.utcnow().timestamp())}"
                
                reasoning_payload = {
                    "overview": f"Potential Credential Harvesting to Account Takeover chain detected for user {user_id}.",
                    "email_evidence": {
                        "email_id": email.email_id,
                        "subject": email.email_subject,
                        "sender": f"{email.sender_name} <{email.sender_email}>",
                        "risk_score": e_analysis.risk_score,
                        "reasons": json.loads(e_analysis.reasons) if e_analysis.reasons else []
                    },
                    "login_evidence": {
                        "event_id": login.event_id,
                        "location": f"{login.city}, {login.country}",
                        "ip": login.ip_address,
                        "risk_score": l_analysis.risk_score,
                        "reasons": json.loads(l_analysis.reasons) if l_analysis.reasons else []
                    },
                    "correlation_analysis": {
                        "time_delta_hours": round(delta_h, 2),
                        "correlation_bonus_applied": risk_res["correlation_bonus"],
                        "bonus_factors": risk_res["bonus_factors"]
                    }
                }
                
                rec_actions = [
                    f"Quarantine Phishing Email {email.email_id}",
                    f"Revoke all active SSO sessions for user {user_id}",
                    f"Force immediate credential reset for user {user_id}",
                    f"Block foreign IP subnet {login.ip_address} on border gateway"
                ]
                
                incident = Incident(
                    incident_id=incident_id,
                    title=f"Suspected Account Compromise: Phishing followed by Foreign Login ({user_id})",
                    affected_user=user_id,
                    risk_score=risk_res["risk_score"],
                    severity=risk_res["severity"],
                    status="New",
                    assigned_analyst="Unassigned",
                    evidence_summary=f"Phishing email '{email.email_subject[:40]}...' arrived {delta_h:.1f} hours before suspicious login from {login.city}, {login.country}.",
                    reasoning=json.dumps(reasoning_payload),
                    recommended_actions=json.dumps(rec_actions),
                    confidence=risk_res["confidence"],
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow()
                )
                db.add(incident)
                db.flush()
                
                # Add Evidence Items
                ev1 = IncidentEvidence(
                    incident_id=incident_id,
                    event_type="email",
                    event_id=email.email_id,
                    evidence_desc=f"Phishing Email: '{email.email_subject}' (Risk: {e_analysis.risk_score})",
                    score_contribution=0.5 * e_analysis.risk_score,
                    timestamp=email.timestamp
                )
                ev2 = IncidentEvidence(
                    incident_id=incident_id,
                    event_type="login",
                    event_id=login.event_id,
                    evidence_desc=f"Suspicious Sign-in: {login.city}, {login.country} ({login.ip_address}) (Risk: {l_analysis.risk_score})",
                    score_contribution=0.5 * l_analysis.risk_score + risk_res["correlation_bonus"],
                    timestamp=login.timestamp
                )
                db.add_all([ev1, ev2])
                
                # Create proposed Response Actions for analyst review
                action1 = ResponseAction(
                    action_id=f"ACT-{incident_id}-1",
                    incident_id=incident_id,
                    action_type="quarantine_email",
                    title="Quarantine Malicious Email",
                    description=f"Remove email {email.email_id} from {user_id}'s mailbox to prevent credential disclosure.",
                    target=email.email_id,
                    status="pending",
                    is_simulated=True,
                    initiated_by="Correlation Engine"
                )
                action2 = ResponseAction(
                    action_id=f"ACT-{incident_id}-2",
                    incident_id=incident_id,
                    action_type="revoke_session",
                    title="Revoke Active Sessions",
                    description=f"Terminate all active OAuth tokens and SAML SSO sessions for {user_id}.",
                    target=user_id,
                    status="pending",
                    is_simulated=True,
                    initiated_by="Correlation Engine"
                )
                action3 = ResponseAction(
                    action_id=f"ACT-{incident_id}-3",
                    incident_id=incident_id,
                    action_type="reset_password",
                    title="Trigger Mandatory Password Reset",
                    description=f"Invalidate password for {user_id} and send out-of-band reset token.",
                    target=user_id,
                    status="pending",
                    is_simulated=True,
                    initiated_by="Correlation Engine"
                )
                db.add_all([action1, action2, action3])
                
                # Audit log
                audit = AuditLog(
                    action="INCIDENT_CORRELATED_AUTO",
                    target_type="incident",
                    target_id=incident_id,
                    actor="System Correlation Engine",
                    details=json.dumps({"affected_user": user_id, "risk_score": risk_res["risk_score"]}),
                    is_simulated=True
                )
                db.add(audit)
                
                db.commit()
                created_incidents.append(incident)
                
        return created_incidents

correlation_engine = CorrelationEngine()
