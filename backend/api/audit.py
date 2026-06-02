from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from models import get_db, AuditLog
from auth.clerk import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])

class AuditLogResponse(BaseModel):
    id: str
    organization_id: str
    user_id: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[str]
    old_values: Optional[dict]
    new_values: Optional[dict]
    created_at: datetime

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    organization_id: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs with optional filters"""
    
    query = db.query(AuditLog).filter(
        AuditLog.organization_id == uuid.UUID(organization_id)
    )
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    if entity_id:
        query = query.filter(AuditLog.entity_id == uuid.UUID(entity_id))
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    query = query.order_by(AuditLog.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    logs = query.all()
    
    return [
        AuditLogResponse(
            id=str(log.id),
            organization_id=str(log.organization_id),
            user_id=str(log.user_id) if log.user_id else None,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=str(log.entity_id) if log.entity_id else None,
            old_values=log.old_values,
            new_values=log.new_values,
            created_at=log.created_at
        )
        for log in logs
    ]

@router.get("/export/{organization_id}")
async def export_audit_logs(
    organization_id: str,
    format: str = Query("csv", pattern="^(csv|json)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export audit logs for compliance"""
    
    query = db.query(AuditLog).filter(
        AuditLog.organization_id == uuid.UUID(organization_id)
    )
    
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    logs = query.order_by(AuditLog.created_at.desc()).all()
    
    if format == "json":
        return {
            "organization_id": organization_id,
            "export_date": datetime.utcnow().isoformat(),
            "log_count": len(logs),
            "logs": [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action,
                    "entity_type": log.entity_type,
                    "entity_id": str(log.entity_id) if log.entity_id else None,
                    "old_values": log.old_values,
                    "new_values": log.new_values,
                    "created_at": log.created_at.isoformat()
                }
                for log in logs
            ]
        }
    else:  # CSV
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "id", "user_id", "action", "entity_type", "entity_id",
            "old_values", "new_values", "created_at"
        ])
        
        for log in logs:
            writer.writerow([
                str(log.id),
                str(log.user_id) if log.user_id else "",
                log.action,
                log.entity_type,
                str(log.entity_id) if log.entity_id else "",
                str(log.old_values) if log.old_values else "",
                str(log.new_values) if log.new_values else "",
                log.created_at.isoformat()
            ])
        
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
        )
