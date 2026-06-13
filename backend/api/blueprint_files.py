from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
import hashlib

from models import get_db, BlueprintFile, Project
from auth.clerk import verify_jwt
from services.storage import storage_service
from services.multi_provider_analyzer import MultiProviderAnalyzer

router = APIRouter(prefix="/blueprint-files", tags=["blueprint-files"])

class BlueprintFileCreate(BaseModel):
    filename: str
    project_id: Optional[str] = None
    analysis_result: Optional[dict] = None
    total_area: Optional[float] = None
    room_count: Optional[int] = None

class BlueprintFileResponse(BaseModel):
    id: str
    filename: str
    project_id: Optional[str]
    status: str
    total_area: Optional[float]
    room_count: Optional[int]
    created_at: datetime
    analyzed_at: Optional[datetime]
    analysis_result: Optional[dict] = None

@router.post("/", response_model=BlueprintFileResponse)
async def create_blueprint_file(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Upload a blueprint file"""

    print(f"Upload request received - file: {file.filename}, project_id: {project_id}")

    # Optional authentication
    if authorization:
        try:
            user = verify_jwt(authorization.replace("Bearer ", ""))
        except Exception as e:
            print(f"Auth failed: {e}")
            pass  # Allow request to proceed even if auth fails

    # Verify project exists if project_id is provided
    project_uuid = None
    if project_id:
        try:
            project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            project_uuid = project.id
            print(f"Project found: {project.id}")
        except Exception as e:
            print(f"Project validation failed: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid project_id: {e}")
    
    # Read file content
    try:
        file_content = await file.read()
        file_size = len(file_content)
        print(f"File read successfully - size: {file_size} bytes")
    except Exception as e:
        print(f"Failed to read file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")
    
    # Validate file size
    from config import MAX_FILE_SIZE_MB
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit"
        )
    
    # Upload to storage
    try:
        storage_path = await storage_service.upload_file(
            file_content,
            file.filename or "unknown",
            file.content_type or "application/octet-stream"
        )
        print(f"File uploaded to storage: {storage_path}")
    except Exception as e:
        print(f"Storage upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {e}")
    
    # Create file record in database
    try:
        new_file = BlueprintFile(
            project_id=uuid.UUID(project_id) if project_id else None,
            filename=file.filename or "unknown",
            file_path=storage_path,
            file_size=file_size,
            status='uploaded'
        )
        
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        print(f"Database record created: {new_file.id}")
    except Exception as e:
        print(f"Database creation failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database creation failed: {e}")
    
    return BlueprintFileResponse(
        id=str(new_file.id),
        filename=new_file.filename,
        project_id=str(new_file.project_id) if new_file.project_id else None,
        status=new_file.status,
        total_area=float(new_file.total_area) if new_file.total_area else None,
        room_count=new_file.room_count,
        created_at=new_file.created_at,
        analyzed_at=new_file.analyzed_at,
        analysis_result=new_file.analysis_result
    )

@router.get("/", response_model=list[BlueprintFileResponse])
async def list_blueprint_files(
    project_id: Optional[str] = None,
    limit: int = 10,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """List recent blueprint files"""
    
    # Optional authentication
    if authorization:
        try:
            from auth.clerk import verify_jwt
            user = verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    query = db.query(BlueprintFile)
    
    if project_id:
        query = query.filter(BlueprintFile.project_id == uuid.UUID(project_id))
    
    query = query.order_by(BlueprintFile.created_at.desc()).limit(limit)
    
    files = query.all()
    
    return [
        BlueprintFileResponse(
            id=str(f.id),
            filename=f.filename,
            project_id=str(f.project_id) if f.project_id else None,
            status=f.status,
            total_area=float(f.total_area) if f.total_area else None,
            room_count=f.room_count,
            created_at=f.created_at,
            analyzed_at=f.analyzed_at,
            analysis_result=f.analysis_result
        )
        for f in files
    ]

@router.get("/{file_id}", response_model=BlueprintFileResponse)
async def get_blueprint_file(
    file_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get blueprint file by ID"""
    
    # Optional authentication
    if authorization:
        try:
            user = verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    file = db.query(BlueprintFile).filter(BlueprintFile.id == uuid.UUID(file_id)).first()
    if not file:
        raise HTTPException(status_code=404, detail="Blueprint file not found")
    
    return BlueprintFileResponse(
        id=str(file.id),
        filename=file.filename,
        project_id=str(file.project_id) if file.project_id else None,
        status=file.status,
        total_area=float(file.total_area) if file.total_area else None,
        room_count=file.room_count,
        created_at=file.created_at,
        analyzed_at=file.analyzed_at,
        analysis_result=file.analysis_result
    )

@router.post("/{file_id}/analyze", response_model=BlueprintFileResponse)
async def analyze_blueprint_file(
    file_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Analyze a blueprint file"""
    
    # Optional authentication
    if authorization:
        try:
            user = verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    file = db.query(BlueprintFile).filter(BlueprintFile.id == uuid.UUID(file_id)).first()
    if not file:
        raise HTTPException(status_code=404, detail="Blueprint file not found")
    
    # Update status to processing
    file.status = 'processing'
    db.commit()

    # Trigger actual analysis with vision analyzer
    try:
        # Read file from storage
        file_data = storage_service.download_file(file.file_path)

        # Initialize multi-provider analyzer
        analyzer = MultiProviderAnalyzer(use_fast_model=True)

        # Analyze the blueprint
        analysis_result = analyzer.analyze_blueprint(file_data, file.filename)

        # Check if analysis failed
        if "error_code" in analysis_result:
            file.status = 'failed'
            file.analysis_result = analysis_result
            db.commit()
            db.refresh(file)
            return BlueprintFileResponse(
                id=str(file.id),
                filename=file.filename,
                project_id=str(file.project_id) if file.project_id else None,
                status=file.status,
                total_area=float(file.total_area) if file.total_area else None,
                room_count=file.room_count,
                created_at=file.created_at,
                analyzed_at=file.analyzed_at,
                analysis_result=file.analysis_result
            )

        # Update file with analysis results
        file.status = 'analyzed'
        file.analyzed_at = datetime.utcnow()

        # Extract rooms and calculate metrics
        rooms = analysis_result.get("rooms", [])
        total_area = sum(room.get("area_px", 0) for room in rooms)

        file.analysis_result = {
            "rooms": rooms,
            "total_area": total_area,
            "room_count": len(rooms),
            "boq": [],  # BOQ will be calculated separately
            "drawing_type": analysis_result.get("drawing_type", "unknown"),
            "scale_detected": analysis_result.get("scale_detected", None),
            "notes": analysis_result.get("notes", "")
        }

        file.total_area = total_area
        file.room_count = len(rooms)

        db.commit()
        db.refresh(file)

    except Exception as e:
        # Handle analysis errors
        file.status = 'failed'
        file.analysis_result = {
            "error_code": "ANALYSIS_FAILED",
            "error_message": str(e),
            "rooms": [],
            "total_area": 0,
            "room_count": 0,
            "boq": []
        }
        db.commit()
        db.refresh(file)
    
    return BlueprintFileResponse(
        id=str(file.id),
        filename=file.filename,
        project_id=str(file.project_id) if file.project_id else None,
        status=file.status,
        total_area=float(file.total_area) if file.total_area else None,
        room_count=file.room_count,
        created_at=file.created_at,
        analyzed_at=file.analyzed_at,
        analysis_result=file.analysis_result
    )

@router.delete("/{file_id}")
async def delete_blueprint_file(
    file_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Delete a blueprint file"""
    
    # Optional authentication
    if authorization:
        try:
            user = verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    file = db.query(BlueprintFile).filter(BlueprintFile.id == uuid.UUID(file_id)).first()
    if not file:
        raise HTTPException(status_code=404, detail="Blueprint file not found")
    
    # Delete from storage if file_path exists
    if file.file_path:
        await storage_service.delete_file(file.file_path)
    
    # Delete from database
    db.delete(file)
    db.commit()
    
    return {"success": True}
