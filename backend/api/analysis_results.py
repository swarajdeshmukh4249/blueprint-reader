from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid

from models import get_db, AnalysisResult, AnalysisVersion, Project
from auth.clerk import get_current_user

router = APIRouter(prefix="/analysis-results", tags=["analysis-results"])

class AnalysisResultCreate(BaseModel):
    project_id: str
    analysis_version_id: str
    total_floor_area: Optional[Decimal] = None
    room_count: Optional[int] = 0
    wall_length: Optional[Decimal] = Decimal("0")
    door_count: Optional[int] = 0
    window_count: Optional[int] = 0
    estimated_material_cost: Optional[Decimal] = Decimal("0")
    estimated_total_cost: Optional[Decimal] = Decimal("0")
    confidence_score: Optional[Decimal] = Decimal("0")
    scale_calibration: Optional[dict] = None
    processing_metadata: Optional[dict] = None

class AnalysisResultUpdate(BaseModel):
    total_floor_area: Optional[Decimal] = None
    room_count: Optional[int] = None
    wall_length: Optional[Decimal] = None
    door_count: Optional[int] = None
    window_count: Optional[int] = None
    estimated_material_cost: Optional[Decimal] = None
    estimated_total_cost: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = None
    scale_calibration: Optional[dict] = None
    processing_metadata: Optional[dict] = None

class AnalysisResultResponse(BaseModel):
    id: str
    project_id: str
    analysis_version_id: str
    total_floor_area: Optional[Decimal]
    room_count: int
    wall_length: Decimal
    door_count: int
    window_count: int
    estimated_material_cost: Decimal
    estimated_total_cost: Decimal
    confidence_score: Decimal
    scale_calibration: dict
    processing_metadata: dict
    created_at: datetime
    updated_at: Optional[datetime]

@router.post("/", response_model=AnalysisResultResponse)
async def create_analysis_result(
    result: AnalysisResultCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new analysis result record"""
    
    # Verify analysis version exists
    analysis = db.query(AnalysisVersion).filter(
        AnalysisVersion.id == uuid.UUID(result.analysis_version_id)
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis version not found")
    
    # Verify project exists
    project = db.query(Project).filter(
        Project.id == uuid.UUID(result.project_id)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if analysis result already exists for this version
    existing = db.query(AnalysisResult).filter(
        AnalysisResult.analysis_version_id == uuid.UUID(result.analysis_version_id)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Analysis result already exists for this analysis version"
        )
    
    new_result = AnalysisResult(
        project_id=uuid.UUID(result.project_id),
        analysis_version_id=uuid.UUID(result.analysis_version_id),
        total_floor_area=result.total_floor_area,
        room_count=result.room_count,
        wall_length=result.wall_length,
        door_count=result.door_count,
        window_count=result.window_count,
        estimated_material_cost=result.estimated_material_cost,
        estimated_total_cost=result.estimated_total_cost,
        confidence_score=result.confidence_score,
        scale_calibration=result.scale_calibration or {},
        processing_metadata=result.processing_metadata or {}
    )
    
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    
    return AnalysisResultResponse(
        id=str(new_result.id),
        project_id=str(new_result.project_id),
        analysis_version_id=str(new_result.analysis_version_id),
        total_floor_area=new_result.total_floor_area,
        room_count=new_result.room_count,
        wall_length=new_result.wall_length,
        door_count=new_result.door_count,
        window_count=new_result.window_count,
        estimated_material_cost=new_result.estimated_material_cost,
        estimated_total_cost=new_result.estimated_total_cost,
        confidence_score=new_result.confidence_score,
        scale_calibration=new_result.scale_calibration,
        processing_metadata=new_result.processing_metadata,
        created_at=new_result.created_at,
        updated_at=new_result.updated_at
    )

@router.get("/{result_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    result_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific analysis result by ID"""
    
    result = db.query(AnalysisResult).filter(
        AnalysisResult.id == uuid.UUID(result_id)
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    return AnalysisResultResponse(
        id=str(result.id),
        project_id=str(result.project_id),
        analysis_version_id=str(result.analysis_version_id),
        total_floor_area=result.total_floor_area,
        room_count=result.room_count,
        wall_length=result.wall_length,
        door_count=result.door_count,
        window_count=result.window_count,
        estimated_material_cost=result.estimated_material_cost,
        estimated_total_cost=result.estimated_total_cost,
        confidence_score=result.confidence_score,
        scale_calibration=result.scale_calibration,
        processing_metadata=result.processing_metadata,
        created_at=result.created_at,
        updated_at=result.updated_at
    )

@router.get("/analysis/{analysis_version_id}", response_model=AnalysisResultResponse)
async def get_analysis_result_by_version(
    analysis_version_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analysis result for a specific analysis version"""
    
    result = db.query(AnalysisResult).filter(
        AnalysisResult.analysis_version_id == uuid.UUID(analysis_version_id)
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found for this version")
    
    return AnalysisResultResponse(
        id=str(result.id),
        project_id=str(result.project_id),
        analysis_version_id=str(result.analysis_version_id),
        total_floor_area=result.total_floor_area,
        room_count=result.room_count,
        wall_length=result.wall_length,
        door_count=result.door_count,
        window_count=result.window_count,
        estimated_material_cost=result.estimated_material_cost,
        estimated_total_cost=result.estimated_total_cost,
        confidence_score=result.confidence_score,
        scale_calibration=result.scale_calibration,
        processing_metadata=result.processing_metadata,
        created_at=result.created_at,
        updated_at=result.updated_at
    )

@router.put("/{result_id}", response_model=AnalysisResultResponse)
async def update_analysis_result(
    result_id: str,
    update: AnalysisResultUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an analysis result record"""
    
    result = db.query(AnalysisResult).filter(
        AnalysisResult.id == uuid.UUID(result_id)
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    if update.total_floor_area is not None:
        result.total_floor_area = update.total_floor_area
    if update.room_count is not None:
        result.room_count = update.room_count
    if update.wall_length is not None:
        result.wall_length = update.wall_length
    if update.door_count is not None:
        result.door_count = update.door_count
    if update.window_count is not None:
        result.window_count = update.window_count
    if update.estimated_material_cost is not None:
        result.estimated_material_cost = update.estimated_material_cost
    if update.estimated_total_cost is not None:
        result.estimated_total_cost = update.estimated_total_cost
    if update.confidence_score is not None:
        result.confidence_score = update.confidence_score
    if update.scale_calibration is not None:
        result.scale_calibration = update.scale_calibration
    if update.processing_metadata is not None:
        result.processing_metadata = update.processing_metadata
    
    result.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(result)
    
    return AnalysisResultResponse(
        id=str(result.id),
        project_id=str(result.project_id),
        analysis_version_id=str(result.analysis_version_id),
        total_floor_area=result.total_floor_area,
        room_count=result.room_count,
        wall_length=result.wall_length,
        door_count=result.door_count,
        window_count=result.window_count,
        estimated_material_cost=result.estimated_material_cost,
        estimated_total_cost=result.estimated_total_cost,
        confidence_score=result.confidence_score,
        scale_calibration=result.scale_calibration,
        processing_metadata=result.processing_metadata,
        created_at=result.created_at,
        updated_at=result.updated_at
    )

@router.delete("/{result_id}")
async def delete_analysis_result(
    result_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an analysis result record"""
    
    result = db.query(AnalysisResult).filter(
        AnalysisResult.id == uuid.UUID(result_id)
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    db.delete(result)
    db.commit()
    
    return {"success": True, "message": "Analysis result deleted successfully"}