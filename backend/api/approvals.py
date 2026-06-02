from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from models import get_db, Approval, User
from auth.clerk import get_current_user

router = APIRouter(prefix="/approvals", tags=["approvals"])

class ApprovalRequest(BaseModel):
    project_id: str
    analysis_version_id: str
    approver_ids: list[str]

class ApprovalResponse(BaseModel):
    id: str
    project_id: str
    analysis_version_id: str
    approver_id: str
    status: str
    comments: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime

@router.post("/request")
async def request_approval(
    request: ApprovalRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request approval for an analysis version"""
    
    # Get user ID from Clerk
    clerk_user_id = current_user.get('sub')
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create approval requests for each approver
    approvals = []
    for approver_id in request.approver_ids:
        approval = Approval(
            project_id=uuid.UUID(request.project_id),
            analysis_version_id=uuid.UUID(request.analysis_version_id),
            approver_id=uuid.UUID(approver_id),
            status='pending'
        )
        db.add(approval)
        approvals.append(approval)
    
    db.commit()
    
    return {
        "success": True,
        "approval_count": len(approvals),
        "message": f"Approval requested from {len(approvals)} approver(s)"
    }

@router.post("/{approval_id}/approve")
async def approve_analysis(
    approval_id: str,
    comments: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve an analysis version"""
    
    approval = db.query(Approval).filter(Approval.id == uuid.UUID(approval_id)).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Check user is the approver
    clerk_user_id = current_user.get('sub')
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user or approval.approver_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to approve this")
    
    approval.status = 'approved'
    approval.comments = comments
    approval.approved_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "status": "approved"}

@router.post("/{approval_id}/reject")
async def reject_analysis(
    approval_id: str,
    comments: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject an analysis version"""
    
    approval = db.query(Approval).filter(Approval.id == uuid.UUID(approval_id)).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Check user is the approver
    clerk_user_id = current_user.get('sub')
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user or approval.approver_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to reject this")
    
    approval.status = 'rejected'
    approval.comments = comments
    db.commit()
    
    return {"success": True, "status": "rejected"}

@router.get("/project/{project_id}", response_model=list[ApprovalResponse])
async def list_project_approvals(
    project_id: str,
    analysis_version_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all approvals for a project"""
    
    query = db.query(Approval).filter(
        Approval.project_id == uuid.UUID(project_id)
    )
    
    if analysis_version_id:
        query = query.filter(Approval.analysis_version_id == uuid.UUID(analysis_version_id))
    
    approvals = query.order_by(Approval.created_at.desc()).all()
    
    return [
        ApprovalResponse(
            id=str(a.id),
            project_id=str(a.project_id),
            analysis_version_id=str(a.analysis_version_id),
            approver_id=str(a.approver_id),
            status=a.status,
            comments=a.comments,
            approved_at=a.approved_at,
            created_at=a.created_at
        )
        for a in approvals
    ]

@router.get("/pending/{user_id}", response_model=list[ApprovalResponse])
async def list_pending_approvals(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List pending approvals for a user"""
    
    approvals = db.query(Approval).filter(
        Approval.approver_id == uuid.UUID(user_id),
        Approval.status == 'pending'
    ).order_by(Approval.created_at.desc()).all()
    
    return [
        ApprovalResponse(
            id=str(a.id),
            project_id=str(a.project_id),
            analysis_version_id=str(a.analysis_version_id),
            approver_id=str(a.approver_id),
            status=a.status,
            comments=a.comments,
            approved_at=a.approved_at,
            created_at=a.created_at
        )
        for a in approvals
    ]
