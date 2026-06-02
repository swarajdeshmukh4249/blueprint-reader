from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid

from models import get_db
from models.public_share import PublicShare
from models.blueprint_file import BlueprintFile
from models.project import Project

router = APIRouter(prefix="/public-shares", tags=["public-shares"])

# Pydantic models
class PublicShareCreate(BaseModel):
    blueprint_file_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    password: Optional[str] = None
    expires_in_days: Optional[int] = None

class PublicShareResponse(BaseModel):
    id: str
    share_token: str
    blueprint_file_id: str
    project_id: str
    title: Optional[str]
    description: Optional[str]
    has_password: bool
    expires_at: Optional[datetime]
    view_count: int
    last_viewed_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    share_url: str

class PublicShareViewResponse(BaseModel):
    title: Optional[str]
    description: Optional[str]
    filename: str
    analysis_result: dict
    total_area: Optional[float]
    room_count: Optional[int]
    boq_total: Optional[float]
    viewed_at: datetime

@router.post("/", response_model=PublicShareResponse)
async def create_public_share(
    share_data: PublicShareCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Create a public share link for a blueprint file"""
    
    # Optional authentication
    user_id = None
    if authorization:
        try:
            from auth.clerk import verify_jwt
            user = verify_jwt(authorization.replace("Bearer ", ""))
            user_id = user.get('id')
        except:
            pass  # Allow request to proceed even if auth fails
    
    # Validate blueprint file exists and is analyzed
    try:
        file_uuid = uuid.UUID(share_data.blueprint_file_id)
        file = db.query(BlueprintFile).filter(BlueprintFile.id == file_uuid).first()
        
        if not file:
            raise HTTPException(status_code=404, detail="Blueprint file not found")
        
        if file.status != 'analyzed':
            raise HTTPException(status_code=400, detail="Only analyzed files can be shared")
        
        if not file.analysis_result:
            raise HTTPException(status_code=400, detail="File has no analysis result to share")
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid blueprint file ID")
    
    # Calculate expiration if provided
    expires_at = None
    if share_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=share_data.expires_in_days)
    
    # Generate unique token
    token = PublicShare.generate_token()
    
    # Create share record
    share = PublicShare(
        share_token=token,
        blueprint_file_id=file_uuid,
        project_id=file.project_id,
        title=share_data.title,
        description=share_data.description,
        password=share_data.password,
        expires_at=expires_at,
        created_by=user_id
    )
    
    db.add(share)
    db.commit()
    db.refresh(share)
    
    # Construct share URL
    share_url = f"{share_data.title or 'BOQ Share'}/share/{token}" if share_data.title else f"/share/{token}"
    
    return PublicShareResponse(
        id=str(share.id),
        share_token=share.share_token,
        blueprint_file_id=str(share.blueprint_file_id),
        project_id=str(share.project_id),
        title=share.title,
        description=share.description,
        has_password=bool(share.password),
        expires_at=share.expires_at,
        view_count=share.view_count,
        last_viewed_at=share.last_viewed_at,
        is_active=share.is_active,
        created_at=share.created_at,
        share_url=share_url
    )

@router.get("/project/{project_id}", response_model=List[PublicShareResponse])
async def list_project_shares(
    project_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """List all public shares for a project"""
    
    # Optional authentication
    if authorization:
        try:
            from auth.clerk import verify_jwt
            verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    shares = db.query(PublicShare).filter(
        PublicShare.project_id == project_uuid
    ).order_by(PublicShare.created_at.desc()).all()
    
    return [
        PublicShareResponse(
            id=str(s.id),
            share_token=s.share_token,
            blueprint_file_id=str(s.blueprint_file_id),
            project_id=str(s.project_id),
            title=s.title,
            description=s.description,
            has_password=bool(s.password),
            expires_at=s.expires_at,
            view_count=s.view_count,
            last_viewed_at=s.last_viewed_at,
            is_active=s.is_active,
            created_at=s.created_at,
            share_url=f"/share/{s.share_token}"
        )
        for s in shares
    ]

@router.get("/{share_id}", response_model=PublicShareResponse)
async def get_share(
    share_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get a specific share by ID"""
    
    # Optional authentication
    if authorization:
        try:
            from auth.clerk import verify_jwt
            verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    try:
        share_uuid = uuid.UUID(share_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid share ID")
    
    share = db.query(PublicShare).filter(PublicShare.id == share_uuid).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    return PublicShareResponse(
        id=str(share.id),
        share_token=share.share_token,
        blueprint_file_id=str(share.blueprint_file_id),
        project_id=str(share.project_id),
        title=share.title,
        description=share.description,
        has_password=bool(share.password),
        expires_at=share.expires_at,
        view_count=share.view_count,
        last_viewed_at=share.last_viewed_at,
        is_active=share.is_active,
        created_at=share.created_at,
        share_url=f"/share/{share.share_token}"
    )

@router.delete("/{share_id}")
async def delete_share(
    share_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Delete a public share"""
    
    # Optional authentication
    if authorization:
        try:
            from auth.clerk import verify_jwt
            verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    try:
        share_uuid = uuid.UUID(share_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid share ID")
    
    share = db.query(PublicShare).filter(PublicShare.id == share_uuid).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    db.delete(share)
    db.commit()
    
    return {"message": "Share deleted successfully"}

@router.patch("/{share_id}/deactivate")
async def deactivate_share(
    share_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Deactivate a public share without deleting it"""
    
    # Optional authentication
    if authorization:
        try:
            from auth.clerk import verify_jwt
            verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    try:
        share_uuid = uuid.UUID(share_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid share ID")
    
    share = db.query(PublicShare).filter(PublicShare.id == share_uuid).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    share.is_active = False
    db.commit()
    
    return {"message": "Share deactivated successfully"}

# Public endpoint for viewing shared content (no auth required)
@router.get("/public/{share_token}", response_model=PublicShareViewResponse)
async def view_public_share(
    share_token: str,
    password: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """View a publicly shared BOQ (no authentication required)"""
    
    share = db.query(PublicShare).filter(PublicShare.share_token == share_token).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    # Check if share is active
    if not share.is_active:
        raise HTTPException(status_code=403, detail="This share has been deactivated")
    
    # Check if share has expired
    if share.expires_at and share.expires_at < datetime.utcnow():
        raise HTTPException(status_code=403, detail="This share has expired")
    
    # Check password if required
    if share.password and share.password != password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # Get the blueprint file
    file = db.query(BlueprintFile).filter(BlueprintFile.id == share.blueprint_file_id).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="Associated file not found")
    
    # Update view count
    share.view_count += 1
    share.last_viewed_at = datetime.utcnow()
    db.commit()
    
    # Calculate BOQ total
    boq_total = None
    if file.analysis_result and file.analysis_result.get('boq'):
        boq_total = sum(item.get('amount', 0) or 0 for item in file.analysis_result['boq'])
    
    return PublicShareViewResponse(
        title=share.title,
        description=share.description,
        filename=file.filename,
        analysis_result=file.analysis_result or {},
        total_area=file.total_area,
        room_count=file.room_count,
        boq_total=boq_total,
        viewed_at=datetime.utcnow()
    )
