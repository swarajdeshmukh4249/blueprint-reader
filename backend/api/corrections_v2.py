from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from models import get_db, Correction, AnalysisVersion, Project, Room, Dimension, Opening, DetectedObject, BOQItem
from auth.clerk import get_current_user

router = APIRouter(prefix="/corrections-v2", tags=["corrections-v2"])

class CorrectionCreate(BaseModel):
    project_id: str
    analysis_version_id: str
    target_table: str
    target_id: str
    field: str
    corrected_value: str
    correction_reason: Optional[str] = None
    properties: Optional[dict] = None

class CorrectionResponse(BaseModel):
    id: str
    project_id: str
    analysis_version_id: str
    target_table: str
    target_id: str
    field: str
    original_value: Optional[str]
    corrected_value: str
    corrected_at: datetime
    corrected_by_user_id: str
    correction_reason: Optional[str]
    properties: dict

@router.post("/", response_model=CorrectionResponse)
async def create_correction(
    correction: CorrectionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new correction record and update the target entity"""
    
    # Verify analysis version exists
    analysis = db.query(AnalysisVersion).filter(
        AnalysisVersion.id == uuid.UUID(correction.analysis_version_id)
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis version not found")
    
    # Verify project exists
    project = db.query(Project).filter(
        Project.id == uuid.UUID(correction.project_id)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate target table
    valid_tables = ['rooms', 'dimensions', 'openings', 'detected_objects', 'boq_items']
    if correction.target_table not in valid_tables:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid target_table. Must be one of: {', '.join(valid_tables)}"
        )
    
    # Get the original value from the target entity
    target_model = {
        'rooms': Room,
        'dimensions': Dimension,
        'openings': Opening,
        'detected_objects': DetectedObject,
        'boq_items': BOQItem
    }.get(correction.target_table)
    
    if not target_model:
        raise HTTPException(status_code=400, detail="Invalid target table")
    
    target_entity = db.query(target_model).filter(
        target_model.id == uuid.UUID(correction.target_id)
    ).first()
    
    if not target_entity:
        raise HTTPException(status_code=404, detail=f"Target entity not found in {correction.target_table}")
    
    # Get original value
    original_value = getattr(target_entity, correction.field, None)
    if original_value is not None:
        original_value = str(original_value)
    
    # Update the target entity
    setattr(target_entity, correction.field, correction.corrected_value)
    
    # Set is_user_corrected flag if the field exists
    if hasattr(target_entity, 'is_user_corrected'):
        setattr(target_entity, 'is_user_corrected', True)
    
    # Update updated_at if the field exists
    if hasattr(target_entity, 'updated_at'):
        setattr(target_entity, 'updated_at', datetime.utcnow())
    
    # Create correction record
    new_correction = Correction(
        project_id=uuid.UUID(correction.project_id),
        analysis_version_id=uuid.UUID(correction.analysis_version_id),
        target_table=correction.target_table,
        target_id=uuid.UUID(correction.target_id),
        field=correction.field,
        original_value=original_value,
        corrected_value=correction.corrected_value,
        corrected_by_user_id=uuid.UUID(current_user['user_id']),
        correction_reason=correction.correction_reason,
        properties=correction.properties or {}
    )
    
    db.add(new_correction)
    db.commit()
    db.refresh(new_correction)
    
    # Trigger dependent recalculation if needed
    _recalculate_dependent_analysis_results(db, analysis.id)
    
    return CorrectionResponse(
        id=str(new_correction.id),
        project_id=str(new_correction.project_id),
        analysis_version_id=str(new_correction.analysis_version_id),
        target_table=new_correction.target_table,
        target_id=str(new_correction.target_id),
        field=new_correction.field,
        original_value=new_correction.original_value,
        corrected_value=new_correction.corrected_value,
        corrected_at=new_correction.corrected_at,
        corrected_by_user_id=str(new_correction.corrected_by_user_id),
        correction_reason=new_correction.correction_reason,
        properties=new_correction.properties
    )

def _recalculate_dependent_analysis_results(db: Session, analysis_version_id: uuid.UUID):
    """Recalculate analysis results when corrections are made"""
    from models import AnalysisResult, Room
    
    # Get or create analysis results
    analysis_result = db.query(AnalysisResult).filter(
        AnalysisResult.analysis_version_id == analysis_version_id
    ).first()
    
    if not analysis_result:
        return
    
    # Recalculate room-based metrics
    rooms = db.query(Room).filter(
        Room.analysis_version_id == analysis_version_id,
        Room.is_deleted == False
    ).all()
    
    total_floor_area = sum(room.area_sqft or 0 for room in rooms)
    room_count = len(rooms)
    
    # Update analysis results
    analysis_result.total_floor_area = total_floor_area
    analysis_result.room_count = room_count
    analysis_result.updated_at = datetime.utcnow()
    
    db.commit()

@router.get("/{correction_id}", response_model=CorrectionResponse)
async def get_correction(
    correction_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific correction by ID"""
    
    correction = db.query(Correction).filter(
        Correction.id == uuid.UUID(correction_id)
    ).first()
    
    if not correction:
        raise HTTPException(status_code=404, detail="Correction not found")
    
    return CorrectionResponse(
        id=str(correction.id),
        project_id=str(correction.project_id),
        analysis_version_id=str(correction.analysis_version_id),
        target_table=correction.target_table,
        target_id=str(correction.target_id),
        field=correction.field,
        original_value=correction.original_value,
        corrected_value=correction.corrected_value,
        corrected_at=correction.corrected_at,
        corrected_by_user_id=str(correction.corrected_by_user_id),
        correction_reason=correction.correction_reason,
        properties=correction.properties
    )

@router.get("/analysis/{analysis_version_id}", response_model=List[CorrectionResponse])
async def get_corrections_by_analysis(
    analysis_version_id: str,
    target_table: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all corrections for a specific analysis version, optionally filtered by table"""
    
    query = db.query(Correction).filter(
        Correction.analysis_version_id == uuid.UUID(analysis_version_id)
    )
    
    if target_table:
        query = query.filter(Correction.target_table == target_table)
    
    corrections = query.order_by(Correction.corrected_at.desc()).all()
    
    return [
        CorrectionResponse(
            id=str(c.id),
            project_id=str(c.project_id),
            analysis_version_id=str(c.analysis_version_id),
            target_table=c.target_table,
            target_id=str(c.target_id),
            field=c.field,
            original_value=c.original_value,
            corrected_value=c.corrected_value,
            corrected_at=c.corrected_at,
            corrected_by_user_id=str(c.corrected_by_user_id),
            correction_reason=c.correction_reason,
            properties=c.properties
        )
        for c in corrections
    ]

@router.get("/target/{target_table}/{target_id}", response_model=List[CorrectionResponse])
async def get_corrections_by_target(
    target_table: str,
    target_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all corrections for a specific target entity"""
    
    # Validate target table
    valid_tables = ['rooms', 'dimensions', 'openings', 'detected_objects', 'boq_items']
    if target_table not in valid_tables:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid target_table. Must be one of: {', '.join(valid_tables)}"
        )
    
    corrections = db.query(Correction).filter(
        Correction.target_table == target_table,
        Correction.target_id == uuid.UUID(target_id)
    ).order_by(Correction.corrected_at.desc()).all()
    
    return [
        CorrectionResponse(
            id=str(c.id),
            project_id=str(c.project_id),
            analysis_version_id=str(c.analysis_version_id),
            target_table=c.target_table,
            target_id=str(c.target_id),
            field=c.field,
            original_value=c.original_value,
            corrected_value=c.corrected_value,
            corrected_at=c.corrected_at,
            corrected_by_user_id=str(c.corrected_by_user_id),
            correction_reason=c.correction_reason,
            properties=c.properties
        )
        for c in corrections
    ]