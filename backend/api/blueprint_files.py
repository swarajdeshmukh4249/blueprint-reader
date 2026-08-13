from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
import uuid
import hashlib

from models import get_db, BlueprintFile, Project, User, OrganizationMember, AnalysisVersion, BOQItem, Room
from auth.clerk import verify_jwt, get_current_user_db
from services.storage import storage_service
from services.multi_provider_analyzer import MultiProviderAnalyzer
from utils.org_filtering import get_user_organizations

router = APIRouter(prefix="/blueprint-files", tags=["blueprint-files"])

class BlueprintFileCreate(BaseModel):
    filename: str
    project_id: Optional[str] = None
    analysis_result: Optional[dict] = None
    total_area: Optional[float] = None
    room_count: Optional[int] = None

class SaveAnalysisRequest(BaseModel):
    filename: str
    project_id: Optional[str] = None
    analysis_result: dict
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


def _as_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _metrics_from_analysis(result: dict, total_area: Optional[float], room_count: Optional[int]):
    """Normalize totals from either UI shape or raw blueprint_logic payload."""
    totals = result.get("totals") if isinstance(result.get("totals"), dict) else {}
    raw = result.get("raw") if isinstance(result.get("raw"), dict) else result

    area = (
        _as_float(total_area)
        or _as_float(totals.get("total_area"))
        or _as_float(result.get("total_area"))
        or _as_float(raw.get("total_area"))
    )

    rooms = result.get("rooms") or result.get("room_data") or raw.get("room_data") or []
    count = room_count
    if count is None:
        count = totals.get("room_count")
    if count is None and isinstance(rooms, list):
        count = len(rooms)

    costs = result.get("costs") if isinstance(result.get("costs"), dict) else {}
    if not costs and isinstance(raw.get("costs"), dict):
        costs = raw["costs"]

    total_cost = (
        _as_float(totals.get("boq_total"))
        or _as_float(result.get("total_cost"))
        or _as_float(raw.get("total_cost"))
        or _as_float(costs.get("Total Estimated Cost"))
    )

    boq = result.get("boq") or raw.get("boq") or raw.get("boq_items") or []
    if not isinstance(boq, list):
        boq = []

    materials = result.get("materials") if isinstance(result.get("materials"), dict) else {}
    if not materials and isinstance(raw.get("materials"), dict):
        materials = raw["materials"]

    return {
        "total_area": area,
        "room_count": int(count) if count is not None else None,
        "total_cost": total_cost,
        "boq": boq,
        "materials": materials,
        "rooms": rooms if isinstance(rooms, list) else [],
        "raw_result": result,
    }


def _ensure_project_for_user(
    db: Session,
    current_user: User,
    project_id: Optional[str],
) -> Project:
    """Attach analysis to a project the user owns; create a default one if needed."""
    org_ids = get_user_organizations(current_user.id, db)
    if not org_ids:
        raise HTTPException(status_code=400, detail="User has no organization")

    if project_id:
        try:
            project_uuid = uuid.UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id format")
        project = db.query(Project).filter(Project.id == project_uuid).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.organization_id not in org_ids:
            raise HTTPException(status_code=403, detail="No access to this project")
        return project

    # Prefer an existing project in the user's orgs
    existing = (
        db.query(Project)
        .filter(Project.organization_id.in_(org_ids), Project.deleted_at.is_(None))
        .order_by(Project.created_at.desc())
        .first()
    )
    if existing:
        return existing

    project = Project(
        organization_id=org_ids[0],
        name="My Analyses",
        building_type="residential",
        status="active",
        created_by=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.post("/save-analysis", response_model=BlueprintFileResponse)
async def save_analysis_result(
    request: SaveAnalysisRequest,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db),
):
    """Persist upload/analyze results so Dashboard + Analytics can show them."""
    metrics = _metrics_from_analysis(
        request.analysis_result or {},
        request.total_area,
        request.room_count,
    )
    project = _ensure_project_for_user(db, current_user, request.project_id)

    try:
        new_file = BlueprintFile(
            project_id=project.id,
            filename=request.filename,
            file_path="",
            file_size=0,
            status="analyzed",
            analysis_result=request.analysis_result,
            total_area=metrics["total_area"],
            room_count=metrics["room_count"],
            analyzed_at=datetime.utcnow(),
        )
        db.add(new_file)
        db.flush()

        last_version = (
            db.query(AnalysisVersion)
            .filter(AnalysisVersion.project_id == project.id)
            .order_by(AnalysisVersion.version_number.desc())
            .first()
        )
        version_number = (last_version.version_number + 1) if last_version else 1

        analysis = AnalysisVersion(
            project_id=project.id,
            blueprint_file_id=new_file.id,
            version_number=version_number,
            name=request.filename,
            status="completed",
            total_area_sqft=metrics["total_area"],
            room_count=metrics["room_count"],
            raw_result={
                **(metrics["raw_result"] if isinstance(metrics["raw_result"], dict) else {}),
                "total_cost": metrics["total_cost"],
            },
            created_by=current_user.id,
            user_id=current_user.id,
            file_name=request.filename,
            progress=100,
            completed_at=datetime.utcnow(),
        )
        db.add(analysis)
        db.flush()

        # Persist rooms when present
        for room in metrics["rooms"]:
            if not isinstance(room, dict):
                continue
            name = room.get("name") or room.get("room") or room.get("label") or "Room"
            db.add(
                Room(
                    analysis_version_id=analysis.id,
                    name=str(name),
                    room_type=str(room.get("room_type") or room.get("type") or "") or None,
                    area_sqft=_as_float(room.get("area")),
                    width_ft=_as_float(room.get("width")),
                    height_ft=_as_float(room.get("height")),
                    source=str(room.get("source") or "upload"),
                    confidence_score=_as_float(room.get("confidence")),
                )
            )

        # Persist BOQ lines when present
        for item in metrics["boq"]:
            if not isinstance(item, dict):
                continue
            description = (
                item.get("description")
                or item.get("item")
                or item.get("material_name")
                or item.get("category")
                or "BOQ item"
            )
            db.add(
                BOQItem(
                    analysis_version_id=analysis.id,
                    category=str(item.get("category") or "General"),
                    item_code=str(item.get("item_code") or item.get("code") or "") or None,
                    description=str(description),
                    unit=str(item.get("unit") or "nos"),
                    quantity=_as_float(item.get("quantity")),
                    rate=_as_float(item.get("rate")),
                    amount=_as_float(item.get("amount")),
                    source="upload_analyze",
                )
            )

        # If no BOQ rows but we have a total cost, store a summary line so cost KPIs work
        if not metrics["boq"] and metrics["total_cost"]:
            db.add(
                BOQItem(
                    analysis_version_id=analysis.id,
                    category="Estimated",
                    description="Total estimated construction cost",
                    unit="ls",
                    quantity=1,
                    rate=metrics["total_cost"],
                    amount=metrics["total_cost"],
                    source="upload_analyze_summary",
                )
            )

        # Material quantities as BOQ-like rows (for material charts)
        if metrics["materials"] and not metrics["boq"]:
            for name, qty in metrics["materials"].items():
                amount = _as_float(qty)
                if amount is None:
                    continue
                db.add(
                    BOQItem(
                        analysis_version_id=analysis.id,
                        category="Materials",
                        description=str(name),
                        unit="unit",
                        quantity=amount,
                        rate=0,
                        amount=0,
                        source="upload_analyze_materials",
                    )
                )

        if project.status == "draft":
            project.status = "active"

        db.commit()
        db.refresh(new_file)
        print(f"Analysis saved: file={new_file.id} analysis={analysis.id} project={project.id}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Failed to save analysis: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save analysis: {e}")

    return BlueprintFileResponse(
        id=str(new_file.id),
        filename=new_file.filename,
        project_id=str(new_file.project_id) if new_file.project_id else None,
        status=new_file.status,
        total_area=float(new_file.total_area) if new_file.total_area else None,
        room_count=new_file.room_count,
        created_at=new_file.created_at,
        analyzed_at=new_file.analyzed_at,
        analysis_result=new_file.analysis_result,
    )


@router.post("/", response_model=BlueprintFileResponse)
async def create_blueprint_file(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    auto_analyze: Optional[bool] = Form(True),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Upload a blueprint file and optionally trigger automatic analysis"""

    if authorization:
        try:
            user = await verify_jwt(authorization.replace("Bearer ", ""))
        except Exception as e:
            print(f"Auth failed: {e}")
            pass  # Allow request to proceed even if auth fails

    print(f"Upload request received - file: {file.filename}, project_id: {project_id}, auto_analyze: {auto_analyze}")

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
    
    # Trigger automatic analysis if requested
    if auto_analyze:
        try:
            print(f"Triggering automatic analysis for file: {new_file.id}")
            from blueprint_logic import analyze_blueprint
            
            # Download file from storage
            file_data = storage_service.download_file(storage_path)
            
            # Run analysis
            analysis_result = analyze_blueprint(file_data, file.filename or "unknown")
            
            # Update file with analysis results
            new_file.status = 'analyzed' if not analysis_result.get('error') else 'failed'
            new_file.analyzed_at = datetime.utcnow()
            
            # Extract key metrics
            rooms = analysis_result.get("room_data", [])
            total_area = sum(room.get("area", 0) for room in rooms)
            
            new_file.analysis_result = analysis_result
            new_file.total_area = total_area
            new_file.room_count = len(rooms)
            
            db.commit()
            db.refresh(new_file)
            print(f"Analysis completed for file: {new_file.id}, status: {new_file.status}")
            
        except Exception as e:
            print(f"Automatic analysis failed: {e}")
            # Don't fail the upload if analysis fails
            new_file.status = 'analysis_failed'
            new_file.analysis_result = {"error": str(e)}
            db.commit()
            db.refresh(new_file)
    
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
    """List recent blueprint files scoped to the authenticated user's organizations."""
    
    # Get current user
    current_user = None
    if authorization:
        try:
            from auth.clerk import verify_jwt
            current_user = await verify_jwt(authorization.replace("Bearer ", ""))
        except Exception:
            pass  # Allow request to proceed even if auth fails
    
    query = db.query(BlueprintFile)
    
    # Filter by user's organizations if authenticated
    if current_user:
        clerk_user_id = current_user.get('sub')
        if clerk_user_id:
            user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
            if user:
                user_org_ids = get_user_organizations(user.id, db)
                
                # INNER join would hide files with no project_id — use outerjoin + org filter
                if user_org_ids:
                    query = query.outerjoin(Project, BlueprintFile.project_id == Project.id).filter(
                        Project.organization_id.in_(user_org_ids)
                    )
                else:
                    query = query.filter(False)
    
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
    
    # Get current user
    current_user = None
    if authorization:
        try:
            current_user = await verify_jwt(authorization.replace("Bearer ", ""))
        except Exception:
            pass  # Allow request to proceed even if auth fails
    
    file = db.query(BlueprintFile).filter(BlueprintFile.id == uuid.UUID(file_id)).first()
    if not file:
        raise HTTPException(status_code=404, detail="Blueprint file not found")
    
    # Check user has access to the file's project
    if current_user:
        clerk_user_id = current_user.get('sub')
        if clerk_user_id:
            from models import User, OrganizationMember
            user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
            if user and file.project_id:
                project = db.query(Project).filter(Project.id == file.project_id).first()
                if project:
                    user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).all()]
                    if project.organization_id not in user_org_ids:
                        raise HTTPException(status_code=403, detail="Access denied to this file")
    
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
            user = await verify_jwt(authorization.replace("Bearer ", ""))
        except Exception:
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
            user = await verify_jwt(authorization.replace("Bearer ", ""))
        except Exception:
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
