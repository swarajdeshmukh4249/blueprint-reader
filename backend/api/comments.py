from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from models import get_db, Comment, User
from auth.clerk import get_current_user

router = APIRouter(prefix="/comments", tags=["comments"])

class CommentCreate(BaseModel):
    project_id: str
    analysis_version_id: Optional[str] = None
    room_id: Optional[str] = None
    boq_item_id: Optional[str] = None
    content: str
    parent_id: Optional[str] = None

class CommentUpdate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: str
    project_id: str
    analysis_version_id: Optional[str]
    room_id: Optional[str]
    boq_item_id: Optional[str]
    user_id: str
    content: str
    parent_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

@router.post("/", response_model=CommentResponse)
async def create_comment(
    comment: CommentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new comment"""
    
    # Get user ID from Clerk
    clerk_user_id = current_user.get('sub')
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_comment = Comment(
        project_id=uuid.UUID(comment.project_id),
        analysis_version_id=uuid.UUID(comment.analysis_version_id) if comment.analysis_version_id else None,
        room_id=uuid.UUID(comment.room_id) if comment.room_id else None,
        boq_item_id=uuid.UUID(comment.boq_item_id) if comment.boq_item_id else None,
        user_id=user.id,
        content=comment.content,
        parent_id=uuid.UUID(comment.parent_id) if comment.parent_id else None
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return CommentResponse(
        id=str(new_comment.id),
        project_id=str(new_comment.project_id),
        analysis_version_id=str(new_comment.analysis_version_id) if new_comment.analysis_version_id else None,
        room_id=str(new_comment.room_id) if new_comment.room_id else None,
        boq_item_id=str(new_comment.boq_item_id) if new_comment.boq_item_id else None,
        user_id=str(new_comment.user_id),
        content=new_comment.content,
        parent_id=str(new_comment.parent_id) if new_comment.parent_id else None,
        created_at=new_comment.created_at,
        updated_at=new_comment.updated_at
    )

@router.get("/project/{project_id}", response_model=list[CommentResponse])
async def get_project_comments(
    project_id: str,
    analysis_version_id: Optional[str] = None,
    room_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comments for a project, optionally filtered"""
    
    query = db.query(Comment).filter(
        Comment.project_id == uuid.UUID(project_id),
        Comment.deleted_at.is_(None)
    )
    
    if analysis_version_id:
        query = query.filter(Comment.analysis_version_id == uuid.UUID(analysis_version_id))
    
    if room_id:
        query = query.filter(Comment.room_id == uuid.UUID(room_id))
    
    comments = query.order_by(Comment.created_at.asc()).all()
    
    return [
        CommentResponse(
            id=str(c.id),
            project_id=str(c.project_id),
            analysis_version_id=str(c.analysis_version_id) if c.analysis_version_id else None,
            room_id=str(c.room_id) if c.room_id else None,
            boq_item_id=str(c.boq_item_id) if c.boq_item_id else None,
            user_id=str(c.user_id),
            content=c.content,
            parent_id=str(c.parent_id) if c.parent_id else None,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in comments
    ]

@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    update: CommentUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a comment"""
    
    comment = db.query(Comment).filter(Comment.id == uuid.UUID(comment_id)).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check user owns the comment
    clerk_user_id = current_user.get('sub')
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user or comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")
    
    comment.content = update.content
    comment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)
    
    return CommentResponse(
        id=str(comment.id),
        project_id=str(comment.project_id),
        analysis_version_id=str(comment.analysis_version_id) if comment.analysis_version_id else None,
        room_id=str(comment.room_id) if comment.room_id else None,
        boq_item_id=str(comment.boq_item_id) if comment.boq_item_id else None,
        user_id=str(comment.user_id),
        content=comment.content,
        parent_id=str(comment.parent_id) if comment.parent_id else None,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )

@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a comment (soft delete)"""
    
    comment = db.query(Comment).filter(Comment.id == uuid.UUID(comment_id)).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check user owns the comment
    clerk_user_id = current_user.get('sub')
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user or comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    
    comment.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}
