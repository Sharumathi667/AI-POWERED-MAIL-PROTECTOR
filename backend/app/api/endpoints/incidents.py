import json
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from backend.app.database.session import get_db
from backend.app.models.entities import (
    Incident, IncidentEvidence, ResponseAction, InvestigationNote,
    AuditLog, EmailEvent, LoginEvent
)
from backend.app.schemas.schemas import IncidentUpdate, InvestigationNoteCreate, IncidentCreate
from backend.app.services.correlation_engine import correlation_engine

router = APIRouter(prefix="/incidents", tags=["Incidents"])

def serialize_incident(inc: Incident, detailed: bool = False) -> dict:
    reasoning_dict = json.loads(inc.reasoning) if inc.reasoning else {}
    rec_actions = json.loads(inc.recommended_actions) if inc.recommended_actions else []
    
    evidence_list = []
    actions_list = []
    notes_list = []
    
    if detailed:
        for ev in inc.evidence_items:
            evidence_list.append({
                "id": ev.id,
                "incident_id": ev.incident_id,
                "event_type": ev.event_type,
                "event_id": ev.event_id,
                "evidence_desc": ev.evidence_desc,
                "score_contribution": ev.score_contribution,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None
            })
            
        for act in inc.actions:
            actions_list.append({
                "id": act.id,
                "action_id": act.action_id,
                "incident_id": act.incident_id,
                "action_type": act.action_type,
                "title": act.title,
                "description": act.description,
                "target": act.target,
                "status": act.status,
                "is_simulated": act.is_simulated,
                "initiated_by": act.initiated_by,
                "approved_by": act.approved_by,
                "execution_result": act.execution_result,
                "created_at": act.created_at.isoformat(),
                "executed_at": act.executed_at.isoformat() if act.executed_at else None
            })
            
        for note in inc.notes:
            notes_list.append({
                "id": note.id,
                "incident_id": note.incident_id,
                "author": note.author,
                "note_text": note.note_text,
                "created_at": note.created_at.isoformat()
            })
            
    return {
        "id": inc.id,
        "incident_id": inc.incident_id,
        "title": inc.title,
        "affected_user": inc.affected_user,
        "risk_score": inc.risk_score,
        "severity": inc.severity,
        "status": inc.status,
        "assigned_analyst": inc.assigned_analyst,
        "evidence_summary": inc.evidence_summary,
        "reasoning": reasoning_dict,
        "recommended_actions": rec_actions,
        "confidence": inc.confidence,
        "created_at": inc.created_at.isoformat(),
        "updated_at": inc.updated_at.isoformat(),
        "evidence_items": evidence_list,
        "actions": actions_list,
        "notes": notes_list
    }

@router.get("")
def list_incidents(
    search: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    user_id: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Incident)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Incident.incident_id.ilike(search_filter),
                Incident.affected_user.ilike(search_filter),
                Incident.title.ilike(search_filter),
                Incident.assigned_analyst.ilike(search_filter)
            )
        )
        
    if status:
        query = query.filter(Incident.status == status)
        
    if severity:
        query = query.filter(Incident.severity == severity)
        
    if user_id:
        query = query.filter(Incident.affected_user == user_id)
        
    total_count = query.count()
    
    order_col = Incident.risk_score if sort_by == "risk_score" else Incident.created_at
    if sort_dir == "desc":
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(asc(order_col))
        
    offset = (page - 1) * limit
    incidents = query.offset(offset).limit(limit).all()
    
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1,
        "items": [serialize_incident(inc, detailed=False) for inc in incidents]
    }

@router.get("/{incident_id}")
def get_incident_details(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return serialize_incident(inc, detailed=True)

@router.patch("/{incident_id}")
def update_incident(incident_id: str, update: IncidentUpdate, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    old_status = inc.status
    if update.status:
        inc.status = update.status
    if update.assigned_analyst:
        inc.assigned_analyst = update.assigned_analyst
    if update.confidence:
        inc.confidence = update.confidence
        
    inc.updated_at = datetime.datetime.utcnow()
    
    audit = AuditLog(
        action="INCIDENT_UPDATED",
        target_type="incident",
        target_id=inc.incident_id,
        actor=inc.assigned_analyst or "Security Analyst",
        details=json.dumps({"old_status": old_status, "new_status": inc.status, "analyst": inc.assigned_analyst}),
        is_simulated=True
    )
    db.add(audit)
    db.commit()
    db.refresh(inc)
    return serialize_incident(inc, detailed=True)

@router.post("/{incident_id}/notes")
def add_incident_note(incident_id: str, note_req: InvestigationNoteCreate, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    note = InvestigationNote(
        incident_id=inc.incident_id,
        author=note_req.author or "Security Analyst",
        note_text=note_req.note_text,
        created_at=datetime.datetime.utcnow()
    )
    db.add(note)
    
    audit = AuditLog(
        action="INVESTIGATION_NOTE_ADDED",
        target_type="incident",
        target_id=inc.incident_id,
        actor=note.author,
        details=json.dumps({"note_excerpt": note.note_text[:100]}),
        is_simulated=True
    )
    db.add(audit)
    db.commit()
    return {"message": "Note added successfully", "note_id": note.id}

@router.get("/{incident_id}/timeline")
def get_incident_timeline(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    timeline = []
    
    # Add linked email and login evidence items
    for ev in inc.evidence_items:
        if ev.event_type == "email":
            em = db.query(EmailEvent).filter(EmailEvent.email_id == ev.event_id).first()
            if em:
                timeline.append({
                    "timestamp": em.timestamp.isoformat(),
                    "type": "email_received",
                    "title": f"Phishing Email Received: {em.email_subject}",
                    "details": f"Sender: {em.sender_name} <{em.sender_email}>. SPF: {em.spf_result}, DKIM: {em.dkim_result}",
                    "badge": "Email Alert",
                    "severity": em.analysis.severity if em.analysis else "high"
                })
        elif ev.event_type == "login":
            lg = db.query(LoginEvent).filter(LoginEvent.event_id == ev.event_id).first()
            if lg:
                timeline.append({
                    "timestamp": lg.timestamp.isoformat(),
                    "type": "login_attempt",
                    "title": f"Suspicious Sign-in: {lg.city}, {lg.country}",
                    "details": f"IP: {lg.ip_address} | Device: {lg.device_type} ({lg.browser}) | Failed attempts: {lg.failed_attempts}",
                    "badge": "Login Anomaly",
                    "severity": lg.analysis.severity if lg.analysis else "critical"
                })
                
    # Add Incident creation
    timeline.append({
        "timestamp": inc.created_at.isoformat(),
        "type": "incident_created",
        "title": f"Security Incident Flagged: {inc.title}",
        "details": f"Correlated with Risk Score: {inc.risk_score} ({inc.severity.upper()}). Assigned to: {inc.assigned_analyst}",
        "badge": "Incident Created",
        "severity": inc.severity
    })
    
    # Add Actions executed
    for act in inc.actions:
        if act.status in ("executed", "rejected"):
            timeline.append({
                "timestamp": act.executed_at.isoformat() if act.executed_at else act.created_at.isoformat(),
                "type": "action_executed",
                "title": f"Response Action {act.status.upper()}: {act.title}",
                "details": act.execution_result or act.description,
                "badge": "Containment Action",
                "severity": "medium" if act.status == "executed" else "low"
            })
            
    # Add Notes
    for n in inc.notes:
        timeline.append({
            "timestamp": n.created_at.isoformat(),
            "type": "analyst_note",
            "title": f"Analyst Note by {n.author}",
            "details": n.note_text,
            "badge": "Analyst Note",
            "severity": "low"
        })
        
    timeline.sort(key=lambda x: x["timestamp"])
    return timeline
