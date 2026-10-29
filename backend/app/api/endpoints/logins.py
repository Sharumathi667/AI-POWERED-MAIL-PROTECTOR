import json
import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from backend.app.database.session import get_db
from backend.app.models.entities import LoginEvent, LoginAnalysis, AuditLog
from backend.app.schemas.schemas import LoginAnalyzeRequest
from backend.app.ml.login_detector import login_detector
from backend.app.services.correlation_engine import correlation_engine

router = APIRouter(prefix="/logins", tags=["Logins"])

def serialize_login(login: LoginEvent) -> dict:
    analysis_data = None
    if login.analysis:
        reasons_list = json.loads(login.analysis.reasons) if login.analysis.reasons else []
        actions_list = json.loads(login.analysis.recommended_actions) if login.analysis.recommended_actions else []
        analysis_data = {
            "id": login.analysis.id,
            "event_id": login.analysis.event_id,
            "anomaly_score": login.analysis.anomaly_score,
            "risk_score": login.analysis.risk_score,
            "severity": login.analysis.severity,
            "is_suspicious": login.analysis.is_suspicious,
            "reasons": reasons_list,
            "recommended_actions": actions_list,
            "location_risk": login.analysis.location_risk,
            "device_risk": login.analysis.device_risk,
            "auth_risk": login.analysis.auth_risk,
            "behavior_risk": login.analysis.behavior_risk,
            "model_version": login.analysis.model_version,
            "analyzed_at": login.analysis.analyzed_at.isoformat()
        }
        
    return {
        "id": login.id,
        "event_id": login.event_id,
        "user_id": login.user_id,
        "timestamp": login.timestamp.isoformat(),
        "ip_address": login.ip_address,
        "country": login.country,
        "city": login.city,
        "device_id": login.device_id,
        "device_type": login.device_type,
        "browser": login.browser,
        "operating_system": login.operating_system,
        "login_success": login.login_success,
        "failed_attempts": login.failed_attempts,
        "is_new_device": login.is_new_device,
        "is_new_location": login.is_new_location,
        "distance_from_usual_location_km": login.distance_from_usual_location_km,
        "minutes_since_previous_login": login.minutes_since_previous_login,
        "impossible_travel": login.impossible_travel,
        "label": login.label,
        "data_source": login.data_source,
        "analysis": analysis_data
    }

@router.get("")
def list_logins(
    search: Optional[str] = None,
    user_id: Optional[str] = None,
    country: Optional[str] = None,
    severity: Optional[str] = None,
    is_suspicious: Optional[bool] = None,
    impossible_travel: Optional[int] = None,
    sort_by: str = Query("timestamp"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(LoginEvent).outerjoin(LoginAnalysis)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                LoginEvent.user_id.ilike(search_filter),
                LoginEvent.event_id.ilike(search_filter),
                LoginEvent.ip_address.ilike(search_filter),
                LoginEvent.city.ilike(search_filter),
                LoginEvent.country.ilike(search_filter)
            )
        )
        
    if user_id:
        query = query.filter(LoginEvent.user_id == user_id)
        
    if country:
        query = query.filter(LoginEvent.country.ilike(f"%{country}%"))
        
    if severity:
        query = query.filter(LoginAnalysis.severity == severity)
        
    if is_suspicious is not None:
        query = query.filter(LoginAnalysis.is_suspicious == is_suspicious)
        
    if impossible_travel is not None:
        query = query.filter(LoginEvent.impossible_travel == impossible_travel)
        
    total_count = query.count()
    
    if sort_by == "risk_score":
        order_col = LoginAnalysis.risk_score
    elif sort_by == "failed_attempts":
        order_col = LoginEvent.failed_attempts
    elif sort_by == "distance":
        order_col = LoginEvent.distance_from_usual_location_km
    else:
        order_col = LoginEvent.timestamp
        
    if sort_dir == "desc":
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(asc(order_col))
        
    offset = (page - 1) * limit
    logins = query.offset(offset).limit(limit).all()
    
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1,
        "items": [serialize_login(l) for l in logins]
    }

@router.get("/{event_id}")
def get_login_details(event_id: str, db: Session = Depends(get_db)):
    login = db.query(LoginEvent).filter(LoginEvent.event_id == event_id).first()
    if not login:
        raise HTTPException(status_code=404, detail="Login event not found")
    return serialize_login(login)

@router.post("/analyze")
def analyze_custom_login(req: LoginAnalyzeRequest, db: Session = Depends(get_db)):
    """Analyze real-time login telemetry using Isolation Forest and configurable anomaly heuristics."""
    raw_payload = {
        "timestamp": datetime.datetime.utcnow(),
        "ip_address": req.ip_address,
        "country": req.country,
        "city": req.city,
        "device_id": req.device_id,
        "device_type": req.device_type,
        "browser": req.browser,
        "operating_system": req.operating_system,
        "login_success": req.login_success,
        "failed_attempts": req.failed_attempts,
        "is_new_device": req.is_new_device,
        "is_new_location": req.is_new_location,
        "distance_from_usual_location_km": req.distance_from_usual_location_km,
        "minutes_since_previous_login": req.minutes_since_previous_login,
        "impossible_travel": req.impossible_travel
    }
    
    analysis = login_detector.analyze_login(raw_payload)
    
    event_id = f"LOGIN-ADHOC-{int(datetime.datetime.utcnow().timestamp())}"
    new_event = LoginEvent(
        event_id=event_id,
        user_id=req.user_id,
        timestamp=datetime.datetime.utcnow(),
        ip_address=req.ip_address,
        country=req.country,
        city=req.city,
        device_id=req.device_id,
        device_type=req.device_type,
        browser=req.browser,
        operating_system=req.operating_system,
        login_success=req.login_success,
        failed_attempts=req.failed_attempts,
        is_new_device=req.is_new_device,
        is_new_location=req.is_new_location,
        distance_from_usual_location_km=req.distance_from_usual_location_km,
        minutes_since_previous_login=req.minutes_since_previous_login,
        impossible_travel=req.impossible_travel,
        label="suspicious" if analysis["is_suspicious"] else "normal",
        data_source="ad_hoc_telemetry"
    )
    db.add(new_event)
    db.flush()
    
    new_analysis = LoginAnalysis(
        event_id=event_id,
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
    db.add(new_analysis)
    
    # Check if this triggers incident correlation with recent emails
    correlation_engine.correlate_user_events(db, req.user_id)
    
    db.commit()
    return serialize_login(new_event)
