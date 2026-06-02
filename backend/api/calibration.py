from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Tuple
from datetime import datetime
import uuid

from models import get_db, AnalysisVersion, Room
from auth.clerk import get_current_user
from services.scale_calibrator import ScaleCalibrator
from utils.errors import (
    CalibrationPointsError,
    CalibrationDistanceError,
    UnitValidationError
)

router = APIRouter(prefix="/calibration", tags=["calibration"])

class ScaleCalibration(BaseModel):
    pt_a: Tuple[float, float]
    pt_b: Tuple[float, float]
    real_distance: float
    unit: str

class CalibrationResult(BaseModel):
    calibration_id: str
    scale_factor: float
    snapped_scale: Optional[float]
    scale_detected: Optional[str]
    confidence: str
    updated_rooms: list
    boq_preview: dict

@router.post("/analysis/{version_id}")
async def calibrate_scale(
    version_id: str,
    calibration: ScaleCalibration,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate scale factor and apply to analysis"""
    
    calibrator = ScaleCalibrator()
    
    # Validate request
    validation_error = calibrator.validate_calibration_request(
        calibration.pt_a,
        calibration.pt_b,
        calibration.real_distance,
        calibration.unit
    )
    
    if validation_error:
        raise HTTPException(status_code=400, detail=validation_error)
    
    # Verify analysis version exists
    analysis = db.query(AnalysisVersion).filter(
        AnalysisVersion.id == uuid.UUID(version_id)
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis version not found")
    
    # Calculate calibration
    try:
        calibration_result = calibrator.calibrate(
            calibration.pt_a,
            calibration.pt_b,
            calibration.real_distance,
            calibration.unit
        )
    except (CalibrationPointsError, CalibrationDistanceError, UnitValidationError) as e:
        raise HTTPException(status_code=400, detail=e.message)
    
    # Get rooms for this analysis
    rooms = db.query(Room).filter(
        Room.analysis_version_id == uuid.UUID(version_id)
    ).all()
    
    # Recalibrate rooms
    old_scale_factor = analysis.scale_factor or 0.001  # Default if not set
    new_scale_factor = calibration_result["scale_factor"]
    
    updated_rooms, diff_summary = calibrator.recalibrate_rooms(
        [r.__dict__ for r in rooms],
        old_scale_factor,
        new_scale_factor
    )
    
    # Update rooms in database
    for room_data in updated_rooms:
        room = db.query(Room).filter(
            Room.id == uuid.UUID(room_data["id"])
        ).first()
        if room:
            room.width_m = room_data["width_m"]
            room.height_m = room_data["height_m"]
            room.area_m2 = room_data["area_m2"]
            room.needs_calibration = False
    
    # Update analysis
    analysis.scale_factor = new_scale_factor
    analysis.is_calibrated = True
    analysis.calibrated_at = datetime.utcnow()
    
    db.commit()
    
    # Calculate BOQ preview
    from services.boq_calculator import BOQCalculator
    boq_calculator = BOQCalculator()
    boq_preview = boq_calculator.calculate_boq(updated_rooms, new_scale_factor)
    
    return {
        "calibration": calibration_result,
        "updated_rooms": updated_rooms,
        "diff_summary": diff_summary,
        "boq_preview": boq_preview
    }
