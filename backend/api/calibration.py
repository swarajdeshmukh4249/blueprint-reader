from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Tuple
from datetime import datetime
import uuid

from models import get_db, AnalysisVersion, Room, ScaleCalibration
from auth.clerk import get_current_user
from services.scale_calibrator import ScaleCalibrator
from services.calibration_confidence import CalibrationConfidenceService
from utils.errors import (
    CalibrationPointsError,
    CalibrationDistanceError,
    UnitValidationError
)
import os
import json
import urllib.request
import urllib.parse

router = APIRouter(prefix="/calibration", tags=["calibration"])

class ScaleCalibrationInput(BaseModel):
    pt_a: Tuple[float, float]
    pt_b: Tuple[float, float]
    real_distance: float
    unit: str
    reference_type: Optional[str] = "manual"

class CalibrationResult(BaseModel):
    calibration_id: str
    scale_factor: float
    snapped_scale: Optional[float]
    scale_detected: Optional[str]
    confidence: str
    updated_rooms: list
    boq_preview: dict

class ManualScaleCalibrationRequest(BaseModel):
    point_a: dict
    point_b: dict
    real_world_distance: float
    unit: str
    pixel_distance: float
    scale_factor: float

class ManualScaleCalibrationResponse(BaseModel):
    success: bool
    scale_factor: float
    unit: str
    message: str


@router.get("/analysis-jobs/calibrations")
async def list_manual_scale_calibrations(
    current_user: dict = Depends(get_current_user),
):
    """Return the signed-in user's previously saved manual calibrations."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    clerk_user_id = current_user.get("sub")
    if not supabase_url or not supabase_service_key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured")
    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    query = urllib.parse.urlencode({
        "select": "id,created_at,scale_calibration",
        "user_id": f"eq.{clerk_user_id}",
        "scale_calibration": "not.is.null",
        "order": "created_at.desc",
        "limit": "20",
    })
    request = urllib.request.Request(
        url=f"{supabase_url}/rest/v1/analysis_jobs?{query}",
        headers={
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            records = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch calibration history: {exc.reason}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch calibration history: {exc}")

    return [
        {
            "analysis_job_id": row.get("id"),
            "created_at": (row.get("scale_calibration") or {}).get("calibrated_at") or row.get("created_at"),
            **(row.get("scale_calibration") or {}),
        }
        for row in records
    ]

@router.post("/analysis/{version_id}")
async def calibrate_scale(
    version_id: str,
    calibration: ScaleCalibrationInput,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate scale factor and apply to analysis with confidence scoring"""
    
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
    
    # Calculate calibration confidence
    confidence_result = CalibrationConfidenceService.calculate_confidence(
        point1_x=calibration.pt_a[0],
        point1_y=calibration.pt_a[1],
        point2_x=calibration.pt_b[0],
        point2_y=calibration.pt_b[1],
        known_distance=calibration.real_distance,
        known_unit=calibration.unit,
        reference_type=calibration.reference_type or "manual"
    )
    
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
    
    # Store calibration with confidence in database
    scale_calibration = ScaleCalibration(
        analysis_version_id=uuid.UUID(version_id),
        point1_x=calibration.pt_a[0],
        point1_y=calibration.pt_a[1],
        point2_x=calibration.pt_b[0],
        point2_y=calibration.pt_b[1],
        known_distance=calibration.real_distance,
        known_unit=calibration.unit,
        calculated_scale=calibration_result["scale_factor"],
        reference_type=calibration.reference_type or "manual",
        confidence_score=confidence_result["confidence_score"],
        confidence_level=confidence_result["confidence_level"],
        confidence_badge=confidence_result["badge"],
        confidence_warnings=confidence_result["warnings"],
        confidence_factors=confidence_result["factors"]
    )
    db.add(scale_calibration)
    
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
        "confidence": confidence_result,
        "updated_rooms": updated_rooms,
        "diff_summary": diff_summary,
        "boq_preview": boq_preview
    }

@router.post("/analysis-jobs/{job_id}/scale-calibration")
async def manual_scale_calibration(
    job_id: str,
    calibration_data: ManualScaleCalibrationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Manual scale calibration for an analysis job - saves calibration data to analysis_jobs table"""
    
    # Get Supabase credentials
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured")
    
    # Verify job exists and user has access
    clerk_user_id = current_user.get('sub')
    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    
    query = urllib.parse.urlencode({
        "select": "id,user_id,org_id",
        "id": f"eq.{job_id}",
        "user_id": f"eq.{clerk_user_id}"
    })
    url = f"{supabase_url}/rest/v1/analysis_jobs?{query}"
    
    try:
        headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json"
        }
        request = urllib.request.Request(url=url, headers=headers, method="GET")
        
        with urllib.request.urlopen(request, timeout=10) as response:
            jobs = json.loads(response.read().decode("utf-8"))
            
        if not jobs:
            raise HTTPException(status_code=404, detail="Analysis job not found or access denied")
        
        job = jobs[0]
        
        # Verify user_id matches
        if job.get('user_id') != clerk_user_id:
            raise HTTPException(status_code=403, detail="Access denied to this analysis job")
        
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise HTTPException(status_code=404, detail="Analysis job not found")
        raise HTTPException(status_code=500, detail=f"Failed to fetch job: {exc.reason}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch job: {str(e)}")
    
    # Store calibration data in analysis_jobs scale_calibration JSONB column
    calibration_record = {
        "scale_factor": calibration_data.scale_factor,
        "unit": calibration_data.unit,
        "pixel_distance": calibration_data.pixel_distance,
        "real_world_distance": calibration_data.real_world_distance,
        "point_a": calibration_data.point_a,
        "point_b": calibration_data.point_b,
        "calibrated_at": datetime.utcnow().isoformat()
    }
    
    # Update analysis_jobs table via Supabase REST API
    update_query = urllib.parse.urlencode({"id": f"eq.{job_id}"})
    update_url = f"{supabase_url}/rest/v1/analysis_jobs?{update_query}"
    
    try:
        update_body = json.dumps({"scale_calibration": calibration_record}).encode("utf-8")
        update_request = urllib.request.Request(
            url=update_url,
            data=update_body,
            headers=headers,
            method="PATCH"
        )
        
        with urllib.request.urlopen(update_request, timeout=10) as response:
            if response.status not in (200, 204):
                raise HTTPException(status_code=500, detail="Failed to update calibration data")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save calibration: {str(e)}")
    
    return ManualScaleCalibrationResponse(
        success=True,
        scale_factor=calibration_data.scale_factor,
        unit=calibration_data.unit,
        message="Scale calibration applied successfully"
    )
