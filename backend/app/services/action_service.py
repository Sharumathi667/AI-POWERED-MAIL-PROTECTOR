import datetime
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.models.entities import ResponseAction, Incident, AuditLog

class ActionService:
    @staticmethod
    def approve_action(
        db: Session,
        action_id: str,
        analyst_name: str = "Security Administrator",
        notes: str = ""
    ) -> ResponseAction:
        action = db.query(ResponseAction).filter(ResponseAction.action_id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Response action not found")
            
        action.status = "executed"
        action.approved_by = analyst_name
        action.executed_at = datetime.datetime.utcnow()
        
        simulated_msg = (
            f"[SIMULATED ACTION EXECUTED] Action '{action.title}' on target '{action.target}' "
            f"simulated successfully. Provider mock returned status code 200 OK. Notes: {notes}"
        )
        action.execution_result = simulated_msg
        
        # Log to Audit Log
        audit = AuditLog(
            action="RESPONSE_ACTION_APPROVED_AND_EXECUTED",
            target_type="response_action",
            target_id=action.action_id,
            actor=analyst_name,
            details=json.dumps({
                "action_type": action.action_type,
                "target": action.target,
                "incident_id": action.incident_id,
                "notes": notes,
                "is_simulated": True
            }),
            is_simulated=True,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(audit)
        
        # If incident associated, check if all actions are resolved and update incident status
        if action.incident_id:
            incident = db.query(Incident).filter(Incident.incident_id == action.incident_id).first()
            if incident and incident.status == "New":
                incident.status = "Investigating"
                incident.updated_at = datetime.datetime.utcnow()
                
        db.commit()
        db.refresh(action)
        return action

    @staticmethod
    def reject_action(
        db: Session,
        action_id: str,
        analyst_name: str = "Security Administrator",
        notes: str = ""
    ) -> ResponseAction:
        action = db.query(ResponseAction).filter(ResponseAction.action_id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Response action not found")
            
        action.status = "rejected"
        action.approved_by = analyst_name
        action.executed_at = datetime.datetime.utcnow()
        action.execution_result = f"Action rejected by {analyst_name}. Reason: {notes}"
        
        audit = AuditLog(
            action="RESPONSE_ACTION_REJECTED",
            target_type="response_action",
            target_id=action.action_id,
            actor=analyst_name,
            details=json.dumps({"reason": notes}),
            is_simulated=True,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(audit)
        db.commit()
        db.refresh(action)
        return action

action_service = ActionService()
