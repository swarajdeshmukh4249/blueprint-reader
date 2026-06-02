from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid

from models import get_db, AnalysisVersion
from auth.clerk import get_current_user
from services.diff_engine import DiffEngine

router = APIRouter(prefix="/diff", tags=["diff"])

class DiffResponse(BaseModel):
    version1: dict
    version2: dict
    changes: dict
    area_difference: float
    cost_difference: float
    summary: str

@router.post("/compare/{version1_id}/{version2_id}", response_model=DiffResponse)
async def compare_versions(
    version1_id: str,
    version2_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare two analysis versions"""
    
    # Get both versions
    v1 = db.query(AnalysisVersion).filter(AnalysisVersion.id == uuid.UUID(version1_id)).first()
    v2 = db.query(AnalysisVersion).filter(AnalysisVersion.id == uuid.UUID(version2_id)).first()
    
    if not v1 or not v2:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    
    # Verify both belong to same project
    if v1.project_id != v2.project_id:
        raise HTTPException(status_code=400, detail="Versions must belong to the same project")
    
    # Get room data for both versions
    # This would require querying the rooms table
    # For now, we'll use the raw_result JSON
    v1_data = {
        "id": str(v1.id),
        "version_number": v1.version_number,
        "rooms": v1.raw_result.get("rooms", []) if v1.raw_result else [],
        "total_cost": v1.raw_result.get("total_cost", 0) if v1.raw_result else 0
    }
    
    v2_data = {
        "id": str(v2.id),
        "version_number": v2.version_number,
        "rooms": v2.raw_result.get("rooms", []) if v2.raw_result else [],
        "total_cost": v2.raw_result.get("total_cost", 0) if v2.raw_result else 0
    }
    
    # Run diff engine
    diff_engine = DiffEngine()
    diff = diff_engine.compare_versions(v1_data, v2_data)
    
    return DiffResponse(
        version1=v1_data,
        version2=v2_data,
        changes=diff.changes,
        area_difference=diff.area_difference,
        cost_difference=diff.cost_difference,
        summary=diff.summary
    )
