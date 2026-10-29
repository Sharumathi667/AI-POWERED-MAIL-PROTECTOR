import json
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database.session import get_db
from backend.app.models.entities import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("")
def list_audit_logs(
    actor: Optional[str] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if actor:
        query = query.filter(AuditLog.actor.ilike(f"%{actor}%"))
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
        
    total_count = query.count()
    offset = (page - 1) * limit
    logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
    
    items = []
    for l in logs:
        details_dict = {}
        if l.details:
            try:
                details_dict = json.loads(l.details)
            except Exception:
                details_dict = {"raw": l.details}
                
        items.append({
            "id": l.id,
            "action": l.action,
            "target_type": l.target_type,
            "target_id": l.target_id,
            "actor": l.actor,
            "details": details_dict,
            "is_simulated": l.is_simulated,
            "timestamp": l.timestamp.isoformat()
        })
        
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "items": items
    }
