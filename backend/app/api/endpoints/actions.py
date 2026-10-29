import json
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database.session import get_db
from backend.app.models.entities import ResponseAction, Incident, AuditLog
from backend.app.schemas.schemas import ActionApprovalRequest
from backend.app.services.action_service import action_service

router = APIRouter(prefix="/actions", tags=["Actions"])

def serialize_action(act: ResponseAction) -> dict:
    return {
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
    }

@router.get("")
def list_actions(
    status: Optional[str] = None,
    incident_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(ResponseAction)
    if status:
        query = query.filter(ResponseAction.status == status)
    if incident_id:
        query = query.filter(ResponseAction.incident_id == incident_id)
        
    actions = query.order_by(desc(ResponseAction.created_at)).limit(limit).all()
    return [serialize_action(a) for a in actions]

@router.post("/preview")
def preview_action(payload: dict):
    """Provides impact simulation and risk preview for proposed containment action."""
    action_type = payload.get("action_type", "unknown")
    target = payload.get("target", "unknown")
    
    previews = {
        "quarantine_email": {
            "action_type": action_type,
            "target": target,
            "impact_scope": "Individual Mailbox Isolation",
            "estimated_impact": "Prevents user interaction with malicious links; safe to reverse if false positive.",
            "requires_admin_consent": True,
            "simulation_mode": True
        },
        "revoke_session": {
            "action_type": action_type,
            "target": target,
            "impact_scope": "Active User SSO Sessions",
            "estimated_impact": "Immediate logout on all devices; forces re-authentication on next request.",
            "requires_admin_consent": True,
            "simulation_mode": True
        },
        "reset_password": {
            "action_type": action_type,
            "target": target,
            "impact_scope": "Account Credential State",
            "estimated_impact": "User password invalidated; one-time recovery link sent to registered backup phone.",
            "requires_admin_consent": True,
            "simulation_mode": True
        },
        "block_sender": {
            "action_type": action_type,
            "target": target,
            "impact_scope": "Campus-Wide Inbound Gateway",
            "estimated_impact": "Blocks all future incoming emails matching this sender domain.",
            "requires_admin_consent": True,
            "simulation_mode": True
        }
    }
    
    return previews.get(action_type, {
        "action_type": action_type,
        "target": target,
        "impact_scope": "General Containment",
        "estimated_impact": "Standard incident response protocol applied.",
        "requires_admin_consent": True,
        "simulation_mode": True
    })

@router.post("/{action_id}/approve")
def approve_action(
    action_id: str,
    req: ActionApprovalRequest = ActionApprovalRequest(),
    db: Session = Depends(get_db)
):
    action = action_service.approve_action(
        db=db,
        action_id=action_id,
        analyst_name=req.analyst_name or "Security Administrator",
        notes=req.notes or ""
    )
    return serialize_action(action)

@router.post("/{action_id}/reject")
def reject_action(
    action_id: str,
    req: ActionApprovalRequest = ActionApprovalRequest(),
    db: Session = Depends(get_db)
):
    action = action_service.reject_action(
        db=db,
        action_id=action_id,
        analyst_name=req.analyst_name or "Security Administrator",
        notes=req.notes or ""
    )
    return serialize_action(action)
