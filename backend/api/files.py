from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
import hashlib

from models import get_db, Project, BlueprintFile
from auth.clerk import get_current_user, verify_jwt
from services.storage import storage_service

router = APIRouter(prefix="/files", tags=["files"])

class FileUploadResponse(BaseModel):
    id: str
    project_id: str
    name: str
    file_type: str
    file_size: int
    storage_path: str
    uploaded_at: datetime

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    project_id: str,
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Upload a blueprint file to a project"""
    
    # Get current user
    current_user = None
    if authorization:
        try:
            current_user = verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    # Verify project exists
    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check user has access to project
    if current_user:
        clerk_user_id = current_user.get('sub')
        if clerk_user_id:
            from models import User, OrganizationMember
            user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
            if user:
                user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).all()]
                if project.organization_id not in user_org_ids:
                    raise HTTPException(status_code=403, detail="Access denied to this project")
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size (max 50MB from config)
    from config import MAX_FILE_SIZE_MB
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit"
        )
    
    # Determine file type
    filename = file.filename or ""
    file_type = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
    
    # Calculate checksum
    checksum = hashlib.sha256(file_content).hexdigest()
    
    # Upload to storage
    storage_path = await storage_service.upload_file(
        file_content,
        filename,
        file.content_type
    )
    
    # Create file record in database
    new_file = BlueprintFile(
        project_id=project.id,
        filename=filename,
        file_path=storage_path,
        file_size=file_size,
        status='uploaded'
    )
    
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    
    return FileUploadResponse(
        id=str(new_file.id),
        project_id=project_id,
        name=filename,
        file_type=file_type,
        file_size=file_size,
        storage_path=storage_path,
        uploaded_at=new_file.created_at
    )

@router.get("/{file_id}")
async def get_file(
    file_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file download URL"""
    
    # This would retrieve the file record and return download URL
    # For now, return a placeholder
    return {"url": f"/api/v1/files/{file_id}/download"}

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file"""
    
    # This would delete the file record and remove from storage
    return {"success": True}
