from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid

from models import get_db
from models.floor_comparison import FloorComparison, DiffStatus
from models.blueprint_file import BlueprintFile
from models.project import Project
from services.room_matcher import RoomMatcher
from utils.errors import (
    SameFloorError,
    FloorNotFoundError,
    FloorNotAnalyzedError,
    FloorNotCalibratedError
)
from auth.clerk import get_current_user

router = APIRouter(prefix="/floor-comparison", tags=["floor-comparison"])

# Pydantic models
class RoomDiff(BaseModel):
    room_name: str
    room_type: str
    status: str  # match, changed, added, removed
    area_a: Optional[float] = None
    area_b: Optional[float] = None
    area_delta: Optional[float] = None
    dims_a: Optional[tuple] = None
    dims_b: Optional[tuple] = None
    match_confidence: float

class FloorComparisonRequest(BaseModel):
    floor_a_id: str
    floor_b_id: str

class FloorComparisonResponse(BaseModel):
    comparison_id: str
    floor_a: dict
    floor_b: dict
    room_diffs: List[dict]
    summary: dict
    warning: Optional[str] = None

@router.post("/compare")
async def compare_floors(
    request: FloorComparisonRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare two floors using weighted room matching algorithm"""
    
    # Validate that floors are different
    if request.floor_a_id == request.floor_b_id:
        raise SameFloorError()
    
    # Get floor data (from BlueprintFile or AnalysisVersion)
    # For now, we'll use BlueprintFile as the floor source
    floor_a = db.query(BlueprintFile).filter(
        BlueprintFile.id == uuid.UUID(request.floor_a_id)
    ).first()
    
    floor_b = db.query(BlueprintFile).filter(
        BlueprintFile.id == uuid.UUID(request.floor_b_id)
    ).first()
    
    if not floor_a:
        raise FloorNotFoundError(request.floor_a_id)
    
    if not floor_b:
        raise FloorNotFoundError(request.floor_b_id)
    
    # Check if floors have been analyzed
    if not floor_a.analysis_result or not floor_b.analysis_result:
        raise FloorNotAnalyzedError(floor_a.name if floor_a.name else "A")
    
    # Check calibration status (warning, not error)
    if not floor_a.is_calibrated or not floor_b.is_calibrated:
        # This is a warning, not an error
        pass
    
    # Prepare floor data for comparison
    floor_a_data = {
        "id": str(floor_a.id),
        "label": floor_a.name or "Floor A",
        "rooms": floor_a.analysis_result.get("rooms", []),
        "total_area_m2": floor_a.analysis_result.get("total_area", 0),
        "boq_cost": floor_a.analysis_result.get("boq_total", 0)
    }
    
    floor_b_data = {
        "id": str(floor_b.id),
        "label": floor_b.name or "Floor B",
        "rooms": floor_b.analysis_result.get("rooms", []),
        "total_area_m2": floor_b.analysis_result.get("total_area", 0),
        "boq_cost": floor_b.analysis_result.get("boq_total", 0)
    }
    
    # Use RoomMatcher service
    matcher = RoomMatcher()
    comparison_result = matcher.compare_floors(floor_a_data, floor_b_data)
    
    # Save comparison to database
    comparison = FloorComparison(
        id=uuid.uuid4(),
        project_id=floor_a.project_id,
        floor_a_id=uuid.UUID(request.floor_a_id),
        floor_b_id=uuid.UUID(request.floor_b_id),
        floor_a_label=floor_a_data["label"],
        floor_b_label=floor_b_data["label"],
        total_area_a=floor_a_data["total_area_m2"],
        total_area_b=floor_b_data["total_area_m2"],
        area_delta=comparison_result["summary"]["area_delta_m2"],
        boq_cost_a=floor_a_data["boq_cost"],
        boq_cost_b=floor_b_data["boq_cost"],
        cost_delta=comparison_result["summary"]["cost_delta"],
        room_diffs=comparison_result["room_diffs"],
        comparison_type="room_matching",
        created_at=datetime.utcnow()
    )
    
    db.add(comparison)
    db.commit()
    
    return comparison_result
