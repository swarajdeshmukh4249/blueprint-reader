from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import uuid

from models import get_db, Dimension, AnalysisVersion, Project
from auth.clerk import get_current_user

router = APIRouter(prefix="/dimensions", tags=["dimensions"])

class DimensionCreate(BaseModel):
    project_id: str
    analysis_version_id: str
    raw_text: str
    value: Decimal
    unit: str
    blueprint_coordinates: Optional[dict] = None
    linked_room_id: Optional[str] = None
    confidence: Optional[Decimal] = Decimal("0.0")

class DimensionUpdate(BaseModel):
    raw_text: Optional[str] = None
    value: Optional[Decimal] = None
    unit: Optional[str] = None
    blueprint_coordinates: Optional[dict] = None
    linked_room_id: Optional[str] = None
    confidence: Optional[Decimal] = None
    is_user_corrected: Optional[bool] = None

class DimensionResponse(BaseModel):
    id: str
    project_id: str
    analysis_version_id: str
    raw_text: str
    value: Decimal
    unit: str
    blueprint_coordinates: Optional[dict]
    linked_room_id: Optional[str]
    confidence: Decimal
    is_user_corrected: bool
    created_at: datetime
    updated_at: Optional[datetime]

@router.post("/", response_model=DimensionResponse)
async def create_dimension(
    dimension: DimensionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new dimension record"""
    
    # Verify analysis version exists
    analysis = db.query(AnalysisVersion).filter(
        AnalysisVersion.id == uuid.UUID(dimension.analysis_version_id)
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis version not found")
    
    # Verify project exists
    project = db.query(Project).filter(
        Project.id == uuid.UUID(dimension.project_id)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    new_dimension = Dimension(
        project_id=uuid.UUID(dimension.project_id),
        analysis_version_id=uuid.UUID(dimension.analysis_version_id),
        raw_text=dimension.raw_text,
        value=dimension.value,
        unit=dimension.unit,
        blueprint_coordinates=dimension.blueprint_coordinates,
        linked_room_id=uuid.UUID(dimension.linked_room_id) if dimension.linked_room_id else None,
        confidence=dimension.confidence
    )
    
    db.add(new_dimension)
    db.commit()
    db.refresh(new_dimension)
    
    return DimensionResponse(
        id=str(new_dimension.id),
        project_id=str(new_dimension.project_id),
        analysis_version_id=str(new_dimension.analysis_version_id),
        raw_text=new_dimension.raw_text,
        value=new_dimension.value,
        unit=new_dimension.unit,
        blueprint_coordinates=new_dimension.blueprint_coordinates,
        linked_room_id=str(new_dimension.linked_room_id) if new_dimension.linked_room_id else None,
        confidence=new_dimension.confidence,
        is_user_corrected=new_dimension.is_user_corrected,
        created_at=new_dimension.created_at,
        updated_at=new_dimension.updated_at
    )

@router.get("/{dimension_id}", response_model=DimensionResponse)
async def get_dimension(
    dimension_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific dimension by ID"""
    
    dimension = db.query(Dimension).filter(
        Dimension.id == uuid.UUID(dimension_id)
    ).first()
    
    if not dimension:
        raise HTTPException(status_code=404, detail="Dimension not found")
    
    return DimensionResponse(
        id=str(dimension.id),
        project_id=str(dimension.project_id),
        analysis_version_id=str(dimension.analysis_version_id),
        raw_text=dimension.raw_text,
        value=dimension.value,
        unit=dimension.unit,
        blueprint_coordinates=dimension.blueprint_coordinates,
        linked_room_id=str(dimension.linked_room_id) if dimension.linked_room_id else None,
        confidence=dimension.confidence,
        is_user_corrected=dimension.is_user_corrected,
        created_at=dimension.created_at,
        updated_at=dimension.updated_at
    )

@router.get("/analysis/{analysis_version_id}", response_model=List[DimensionResponse])
async def get_dimensions_by_analysis(
    analysis_version_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all dimensions for a specific analysis version"""
    
    dimensions = db.query(Dimension).filter(
        Dimension.analysis_version_id == uuid.UUID(analysis_version_id)
    ).all()
    
    return [
        DimensionResponse(
            id=str(d.id),
            project_id=str(d.project_id),
            analysis_version_id=str(d.analysis_version_id),
            raw_text=d.raw_text,
            value=d.value,
            unit=d.unit,
            blueprint_coordinates=d.blueprint_coordinates,
            linked_room_id=str(d.linked_room_id) if d.linked_room_id else None,
            confidence=d.confidence,
            is_user_corrected=d.is_user_corrected,
            created_at=d.created_at,
            updated_at=d.updated_at
        )
        for d in dimensions
    ]

@router.put("/{dimension_id}", response_model=DimensionResponse)
async def update_dimension(
    dimension_id: str,
    update: DimensionUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a dimension record"""
    
    dimension = db.query(Dimension).filter(
        Dimension.id == uuid.UUID(dimension_id)
    ).first()
    
    if not dimension:
        raise HTTPException(status_code=404, detail="Dimension not found")
    
    if update.raw_text is not None:
        dimension.raw_text = update.raw_text
    if update.value is not None:
        dimension.value = update.value
    if update.unit is not None:
        dimension.unit = update.unit
    if update.blueprint_coordinates is not None:
        dimension.blueprint_coordinates = update.blueprint_coordinates
    if update.linked_room_id is not None:
        dimension.linked_room_id = uuid.UUID(update.linked_room_id) if update.linked_room_id else None
    if update.confidence is not None:
        dimension.confidence = update.confidence
    if update.is_user_corrected is not None:
        dimension.is_user_corrected = update.is_user_corrected
    
    dimension.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(dimension)
    
    return DimensionResponse(
        id=str(dimension.id),
        project_id=str(dimension.project_id),
        analysis_version_id=str(dimension.analysis_version_id),
        raw_text=dimension.raw_text,
        value=dimension.value,
        unit=dimension.unit,
        blueprint_coordinates=dimension.blueprint_coordinates,
        linked_room_id=str(dimension.linked_room_id) if dimension.linked_room_id else None,
        confidence=dimension.confidence,
        is_user_corrected=dimension.is_user_corrected,
        created_at=dimension.created_at,
        updated_at=dimension.updated_at
    )

@router.delete("/{dimension_id}")
async def delete_dimension(
    dimension_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a dimension record"""
    
    dimension = db.query(Dimension).filter(
        Dimension.id == uuid.UUID(dimension_id)
    ).first()
    
    if not dimension:
        raise HTTPException(status_code=404, detail="Dimension not found")
    
    db.delete(dimension)
    db.commit()
    
    return {"success": True, "message": "Dimension deleted successfully"}