import json
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from backend.app.database.session import get_db
from backend.app.models.entities import EmailEvent, EmailAnalysis, LoginEvent, AuditLog
from backend.app.schemas.schemas import EmailAnalyzeRequest
from backend.app.ml.email_classifier import email_classifier
from backend.app.services.correlation_engine import correlation_engine

router = APIRouter(prefix="/emails", tags=["Emails"])

def serialize_email(email: EmailEvent) -> dict:
    analysis_data = None
    if email.analysis:
        reasons_list = json.loads(email.analysis.reasons) if email.analysis.reasons else []
        actions_list = json.loads(email.analysis.recommended_actions) if email.analysis.recommended_actions else []
        analysis_data = {
            "id": email.analysis.id,
            "email_id": email.analysis.email_id,
            "predicted_class": email.analysis.predicted_class,
            "phishing_probability": email.analysis.phishing_probability,
            "risk_score": email.analysis.risk_score,
            "severity": email.analysis.severity,
            "reasons": reasons_list,
            "recommended_actions": actions_list,
            "content_risk": email.analysis.content_risk,
            "url_risk": email.analysis.url_risk,
            "sender_risk": email.analysis.sender_risk,
            "model_version": email.analysis.model_version,
            "analyzed_at": email.analysis.analyzed_at.isoformat()
        }
        
    return {
        "id": email.id,
        "email_id": email.email_id,
        "user_id": email.user_id,
        "timestamp": email.timestamp.isoformat(),
        "sender_name": email.sender_name,
        "sender_email": email.sender_email,
        "sender_domain": email.sender_domain,
        "reply_to": email.reply_to,
        "email_subject": email.email_subject,
        "email_body": email.email_body,
        "urls": email.urls,
        "link_count": email.link_count,
        "has_attachment": email.has_attachment,
        "attachment_type": email.attachment_type,
        "spf_result": email.spf_result,
        "dkim_result": email.dkim_result,
        "dmarc_result": email.dmarc_result,
        "display_name_mismatch": email.display_name_mismatch,
        "domain_age_category": email.domain_age_category,
        "label": email.label,
        "data_source": email.data_source,
        "analysis": analysis_data
    }

@router.get("")
def list_emails(
    search: Optional[str] = None,
    predicted_class: Optional[str] = None,
    severity: Optional[str] = None,
    user_id: Optional[str] = None,
    sort_by: str = Query("timestamp"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(EmailEvent).outerjoin(EmailAnalysis)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                EmailEvent.email_subject.ilike(search_filter),
                EmailEvent.sender_email.ilike(search_filter),
                EmailEvent.sender_name.ilike(search_filter),
                EmailEvent.user_id.ilike(search_filter),
                EmailEvent.email_id.ilike(search_filter)
            )
        )
        
    if predicted_class:
        query = query.filter(EmailAnalysis.predicted_class == predicted_class)
        
    if severity:
        query = query.filter(EmailAnalysis.severity == severity)
        
    if user_id:
        query = query.filter(EmailEvent.user_id == user_id)
        
    total_count = query.count()
    
    # Sorting
    if sort_by == "risk_score":
        order_col = EmailAnalysis.risk_score
    elif sort_by == "email_id":
        order_col = EmailEvent.email_id
    else:
        order_col = EmailEvent.timestamp
        
    if sort_dir == "desc":
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(asc(order_col))
        
    offset = (page - 1) * limit
    emails = query.offset(offset).limit(limit).all()
    
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1,
        "items": [serialize_email(e) for e in emails]
    }

@router.get("/{email_id}")
def get_email_details(email_id: str, db: Session = Depends(get_db)):
    email = db.query(EmailEvent).filter(EmailEvent.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail=f"Email with ID '{email_id}' not found")
        
    # Also fetch recent logins for the same user to show immediate context
    related_logins = (
        db.query(LoginEvent)
        .filter(LoginEvent.user_id == email.user_id)
        .order_by(LoginEvent.timestamp.desc())
        .limit(5)
        .all()
    )
    
    logins_data = []
    for l in related_logins:
        logins_data.append({
            "event_id": l.event_id,
            "timestamp": l.timestamp.isoformat(),
            "ip_address": l.ip_address,
            "location": f"{l.city}, {l.country}",
            "device": f"{l.device_type} ({l.browser} on {l.operating_system})",
            "login_success": l.login_success,
            "impossible_travel": l.impossible_travel,
            "risk_score": l.analysis.risk_score if l.analysis else 0.0,
            "severity": l.analysis.severity if l.analysis else "low"
        })
        
    result = serialize_email(email)
    result["related_logins"] = logins_data
    return result

@router.post("/analyze")
def analyze_custom_email(req: EmailAnalyzeRequest, db: Session = Depends(get_db)):
    """Analyze a new or ad-hoc email payload using the trained ML model and explainable rules."""
    sender_domain = req.sender_email.split("@")[1] if "@" in req.sender_email else "unknown.com"
    
    raw_payload = {
        "email_subject": req.email_subject,
        "email_body": req.email_body,
        "sender_name": req.sender_name or "",
        "sender_email": req.sender_email,
        "sender_domain": sender_domain,
        "reply_to": req.reply_to or req.sender_email,
        "urls": req.urls or "",
        "link_count": req.link_count or 0,
        "has_attachment": req.has_attachment or 0,
        "attachment_type": req.attachment_type or "none",
        "spf_result": req.spf_result or "pass",
        "dkim_result": req.dkim_result or "pass",
        "dmarc_result": req.dmarc_result or "pass",
        "display_name_mismatch": req.display_name_mismatch or 0,
        "domain_age_category": "established_>1y"
    }
    
    analysis = email_classifier.analyze_email(raw_payload)
    
    # Save ad-hoc event
    email_id = f"EMAIL-ADHOC-{int(datetime.datetime.utcnow().timestamp())}"
    new_event = EmailEvent(
        email_id=email_id,
        user_id=req.user_id,
        timestamp=datetime.datetime.utcnow(),
        sender_name=req.sender_name,
        sender_email=req.sender_email,
        sender_domain=sender_domain,
        reply_to=req.reply_to or req.sender_email,
        email_subject=req.email_subject,
        email_body=req.email_body,
        urls=req.urls,
        link_count=req.link_count,
        has_attachment=req.has_attachment,
        attachment_type=req.attachment_type,
        spf_result=req.spf_result,
        dkim_result=req.dkim_result,
        dmarc_result=req.dmarc_result,
        display_name_mismatch=req.display_name_mismatch,
        domain_age_category="established_>1y",
        label=analysis["predicted_class"],
        data_source="ad_hoc_analysis"
    )
    db.add(new_event)
    db.flush()
    
    new_analysis = EmailAnalysis(
        email_id=email_id,
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
    db.add(new_analysis)
    
    # Check if this triggers incident correlation with user's logins
    correlation_engine.correlate_user_events(db, req.user_id)
    
    db.commit()
    return serialize_email(new_event)

@router.post("/{email_id}/reanalyze")
def reanalyze_existing_email(email_id: str, db: Session = Depends(get_db)):
    email = db.query(EmailEvent).filter(EmailEvent.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    raw_payload = {
        "email_subject": email.email_subject,
        "email_body": email.email_body,
        "sender_name": email.sender_name,
        "sender_email": email.sender_email,
        "sender_domain": email.sender_domain,
        "reply_to": email.reply_to,
        "urls": email.urls,
        "link_count": email.link_count,
        "has_attachment": email.has_attachment,
        "attachment_type": email.attachment_type,
        "spf_result": email.spf_result,
        "dkim_result": email.dkim_result,
        "dmarc_result": email.dmarc_result,
        "display_name_mismatch": email.display_name_mismatch,
        "domain_age_category": email.domain_age_category
    }
    
    analysis = email_classifier.analyze_email(raw_payload)
    
    if email.analysis:
        email.analysis.predicted_class = analysis["predicted_class"]
        email.analysis.phishing_probability = analysis["phishing_probability"]
        email.analysis.risk_score = analysis["risk_score"]
        email.analysis.severity = analysis["severity"]
        email.analysis.reasons = json.dumps(analysis["reasons"])
        email.analysis.recommended_actions = json.dumps(analysis["recommended_actions"])
        email.analysis.content_risk = analysis["content_risk"]
        email.analysis.url_risk = analysis["url_risk"]
        email.analysis.sender_risk = analysis["sender_risk"]
        email.analysis.analyzed_at = datetime.datetime.utcnow()
    else:
        new_analysis = EmailAnalysis(
            email_id=email.email_id,
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
        db.add(new_analysis)
        
    audit = AuditLog(
        action="EMAIL_REANALYZED",
        target_type="email",
        target_id=email.email_id,
        actor="Security Analyst",
        details=json.dumps({"new_risk_score": analysis["risk_score"], "class": analysis["predicted_class"]}),
        is_simulated=True
    )
    db.add(audit)
    db.commit()
    return serialize_email(email)
