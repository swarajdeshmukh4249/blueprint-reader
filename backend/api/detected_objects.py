from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import uuid

from models import get_db, DetectedObject, AnalysisVersion, Project
from auth.clerk import get_current_user

router = APIRouter(prefix="/detected-objects", tags=["detected-objects"])

class DetectedObjectCreate(BaseModel):
    project_id: str
    analysis_version_id: str
    object_type: str
    geometry: dict
    confidence: Optional[Decimal] = Decimal("0.0")
    properties: Optional[dict] = None

class DetectedObjectUpdate(BaseModel):
    object_type: Optional[str] = None
    geometry: Optional[dict] = None
    confidence: Optional[Decimal] = None
    properties: Optional[dict] = None

class DetectedObjectResponse(BaseModel):
    id: str
    project_id: str
    analysis_version_id: str
    object_type: str
    geometry: dict
    confidence: Decimal
    properties: dict
    created_at: datetime

@router.post("/", response_model=DetectedObjectResponse)
async def create_detected_object(
    obj: DetectedObjectCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new detected object record"""
    
    # Verify analysis version exists
    analysis = db.query(AnalysisVersion).filter(
        AnalysisVersion.id == uuid.UUID(obj.analysis_version_id)
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis version not found")
    
    # Verify project exists
    project = db.query(Project).filter(
        Project.id == uuid.UUID(obj.project_id)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate object type
    valid_types = ['wall', 'door', 'window', 'column', 'stair', 'furniture', 'other']
    if obj.object_type not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid object_type. Must be one of: {', '.join(valid_types)}"
        )
    
    new_object = DetectedObject(
        project_id=uuid.UUID(obj.project_id),
        analysis_version_id=uuid.UUID(obj.analysis_version_id),
        object_type=obj.object_type,
        geometry=obj.geometry,
        confidence=obj.confidence,
        properties=obj.properties or {}
    )
    
    db.add(new_object)
    db.commit()
    db.refresh(new_object)
    
    return DetectedObjectResponse(
        id=str(new_object.id),
        project_id=str(new_object.project_id),
        analysis_version_id=str(new_object.analysis_version_id),
        object_type=new_object.object_type,
        geometry=new_object.geometry,
        confidence=new_object.confidence,
        properties=new_object.properties,
        created_at=new_object.created_at
    )

@router.get("/{object_id}", response_model=DetectedObjectResponse)
async def get_detected_object(
    object_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific detected object by ID"""
    
    obj = db.query(DetectedObject).filter(
        DetectedObject.id == uuid.UUID(object_id)
    ).first()
    
    if not obj:
        raise HTTPException(status_code=404, detail="Detected object not found")
    
    return DetectedObjectResponse(
        id=str(obj.id),
        project_id=str(obj.project_id),
        analysis_version_id=str(obj.analysis_version_id),
        object_type=obj.object_type,
        geometry=obj.geometry,
        confidence=obj.confidence,
        properties=obj.properties,
        created_at=obj.created_at
    )

@router.get("/analysis/{analysis_version_id}", response_model=List[DetectedObjectResponse])
async def get_detected_objects_by_analysis(
    analysis_version_id: str,
    object_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all detected objects for a specific analysis version, optionally filtered by type"""
    
    query = db.query(DetectedObject).filter(
        DetectedObject.analysis_version_id == uuid.UUID(analysis_version_id)
    )
    
    if object_type:
        query = query.filter(DetectedObject.object_type == object_type)
    
    objects = query.all()
    
    return [
        DetectedObjectResponse(
            id=str(obj.id),
            project_id=str(obj.project_id),
            analysis_version_id=str(obj.analysis_version_id),
            object_type=obj.object_type,
            geometry=obj.geometry,
            confidence=obj.confidence,
            properties=obj.properties,
            created_at=obj.created_at
        )
        for obj in objects
    ]

@router.put("/{object_id}", response_model=DetectedObjectResponse)
async def update_detected_object(
    object_id: str,
    update: DetectedObjectUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a detected object record"""
    
    obj = db.query(DetectedObject).filter(
        DetectedObject.id == uuid.UUID(object_id)
    ).first()
    
    if not obj:
        raise HTTPException(status_code=404, detail="Detected object not found")
    
    if update.object_type is not None:
        # Validate object type
        valid_types = ['wall', 'door', 'window', 'column', 'stair', 'furniture', 'other']
        if update.object_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid object_type. Must be one of: {', '.join(valid_types)}"
            )
        obj.object_type = update.object_type
    if update.geometry is not None:
        obj.geometry = update.geometry
    if update.confidence is not None:
        obj.confidence = update.confidence
    if update.properties is not None:
        obj.properties = update.properties
    
    db.commit()
    db.refresh(obj)
    
    return DetectedObjectResponse(
        id=str(obj.id),
        project_id=str(obj.project_id),
        analysis_version_id=str(obj.analysis_version_id),
        object_type=obj.object_type,
        geometry=obj.geometry,
        confidence=obj.confidence,
        properties=obj.properties,
        created_at=obj.created_at
    )

@router.delete("/{object_id}")
async def delete_detected_object(
    object_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a detected object record"""
    
    obj = db.query(DetectedObject).filter(
        DetectedObject.id == uuid.UUID(object_id)
    ).first()
    
    if not obj:
        raise HTTPException(status_code=404, detail="Detected object not found")
    
    db.delete(obj)
    db.commit()
    
    return {"success": True, "message": "Detected object deleted successfully"}