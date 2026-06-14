from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from models import get_db, Project, Organization, BlueprintFile, AnalysisVersion, User
from auth.clerk import get_current_user, verify_jwt, get_current_user_db, require_organization_role

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    organization_id: str
    name: str
    code: Optional[str] = None
    client_name: Optional[str] = None
    location_country: Optional[str] = None
    location_state: Optional[str] = None
    location_city: Optional[str] = None
    building_type: Optional[str] = None
    unit_system: str = "imperial"

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[dict] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    floor_count: int
    analysis_count: int
    status: str
    estimated_cost: Optional[int]  # in paise
    updated_at: datetime
    thumbnail_url: Optional[str]

class ProjectDetailResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    code: Optional[str]
    client_name: Optional[str]
    location_country: Optional[str]
    location_state: Optional[str]
    location_city: Optional[str]
    building_type: Optional[str]
    unit_system: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

@router.post("/", response_model=ProjectDetailResponse)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(require_organization_role(["admin", "project_manager"])),
    db: Session = Depends(get_db)
):
    """Create a new project (admin or project_manager only)"""
    
    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == uuid.UUID(project.organization_id)).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Create project
    new_project = Project(
        organization_id=uuid.UUID(project.organization_id),
        name=project.name,
        code=project.code,
        client_name=project.client_name,
        location_country=project.location_country,
        location_state=project.location_state,
        location_city=project.location_city,
        building_type=project.building_type,
        unit_system=project.unit_system,
        created_by=current_user.id
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return ProjectDetailResponse(
        id=str(new_project.id),
        organization_id=str(new_project.organization_id),
        name=new_project.name,
        code=new_project.code,
        client_name=new_project.client_name,
        location_country=new_project.location_country,
        location_state=new_project.location_state,
        location_city=new_project.location_city,
        building_type=new_project.building_type,
        unit_system=new_project.unit_system,
        status=new_project.status,
        created_at=new_project.created_at,
        updated_at=new_project.updated_at
    )

@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    limit: int = Query(5, ge=1, le=100),
    sort: str = Query("updated_at:desc", pattern="^[a-z_]+:(asc|desc)$"),
    organization_id: Optional[str] = None,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """List projects for dashboard with limit and sort"""
    
    query = db.query(Project)
    
    # Filter by organization if provided
    if organization_id:
        # Check user has access to this organization
        from auth.clerk import check_organization_access
        if not check_organization_access(str(current_user.id), organization_id, db):
            raise HTTPException(status_code=403, detail="Access denied to this organization")
        query = query.filter(Project.organization_id == uuid.UUID(organization_id))
    else:
        # Only show projects from organizations user has access to
        from models import OrganizationMember
        user_orgs = db.query(OrganizationMember.organization_id).filter(
            OrganizationMember.user_id == current_user.id
        ).all()
        org_ids = [org.organization_id for org in user_orgs]
        if org_ids:
            query = query.filter(Project.organization_id.in_(org_ids))
        else:
            return []  # User has no organization access
    
    # Parse sort parameter
    sort_field, sort_direction = sort.split(":")
    if sort_field == "updated_at":
        if sort_direction == "desc":
            query = query.order_by(Project.updated_at.desc())
        else:
            query = query.order_by(Project.updated_at.asc())
    
    # Apply limit
    query = query.limit(limit)
    
    projects = query.all()
    
    # Build response with dashboard fields
    result = []
    for p in projects:
        # Count floors (blueprint files)
        floor_count = db.query(BlueprintFile).filter(
            BlueprintFile.project_id == p.id
        ).count()
        
        # Count analyses
        analysis_count = db.query(AnalysisVersion).filter(
            AnalysisVersion.project_id == p.id
        ).count()
        
        # Determine status based on spec rules
        # "completed" → all floors analyzed, no unresolved flags
        # "in_progress" → analysis running OR some floors pending
        # "needs_review" → any room has confidence < CONFIDENCE_MEDIUM
        # "failed" → last analysis returned an error
        status = "in_progress"  # Default
        
        # Check if any analysis failed
        failed_analysis = db.query(AnalysisVersion).filter(
            AnalysisVersion.project_id == p.id,
            AnalysisVersion.status == "failed"
        ).first()
        
        if failed_analysis:
            status = "failed"
        elif floor_count > 0 and analysis_count == floor_count:
            # All floors analyzed, check for low confidence rooms
            from config import CONFIDENCE_MEDIUM
            low_confidence_rooms = db.query(AnalysisVersion).filter(
                AnalysisVersion.project_id == p.id
            ).all()
            
            has_low_confidence = False
            for analysis in low_confidence_rooms:
                if analysis.analysis_result:
                    rooms = analysis.analysis_result.get("rooms", [])
                    for room in rooms:
                        if room.get("confidence", 1.0) < CONFIDENCE_MEDIUM:
                            has_low_confidence = True
                            break
                if has_low_confidence:
                    break
            
            if has_low_confidence:
                status = "needs_review"
            else:
                status = "completed"
        
        # Calculate estimated cost from BOQ
        estimated_cost = None
        # This would need to be calculated from BOQ items or stored in project
        # For now, set to None
        
        # Get thumbnail URL (first blueprint file)
        thumbnail_url = None
        first_file = db.query(BlueprintFile).filter(
            BlueprintFile.project_id == p.id
        ).first()
        if first_file and first_file.file_path:
            thumbnail_url = first_file.file_path
        
        result.append(ProjectResponse(
            id=str(p.id),
            name=p.name,
            floor_count=floor_count,
            analysis_count=analysis_count,
            status=status,
            estimated_cost=estimated_cost,
            updated_at=p.updated_at or p.created_at,
            thumbnail_url=thumbnail_url
        ))
    
    return result

@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Get project by ID"""
    
    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check user has access to this project
    from auth.clerk import check_project_access
    if not check_project_access(str(current_user.id), str(project.id), db):
        raise HTTPException(status_code=403, detail="Access denied to this project")
    
    return ProjectDetailResponse(
        id=str(project.id),
        organization_id=str(project.organization_id),
        name=project.name,
        code=project.code,
        client_name=project.client_name,
        location_country=project.location_country,
        location_state=project.location_state,
        location_city=project.location_city,
        building_type=project.building_type,
        unit_system=project.unit_system,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at
    )

@router.put("/{project_id}", response_model=ProjectDetailResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: User = Depends(require_organization_role(["admin", "project_manager"])),
    db: Session = Depends(get_db)
):
    """Update project (admin or project_manager only)"""
    
    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_update.name is not None:
        project.name = project_update.name
    if project_update.client_name is not None:
        project.client_name = project_update.client_name
    if project_update.status is not None:
        project.status = project_update.status
    if project_update.settings is not None:
        project.settings = project_update.settings
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return ProjectDetailResponse(
        id=str(project.id),
        organization_id=str(project.organization_id),
        name=project.name,
        code=project.code,
        client_name=project.client_name,
        location_country=project.location_country,
        location_state=project.location_state,
        location_city=project.location_city,
        building_type=project.building_type,
        unit_system=project.unit_system,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at
    )

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(require_organization_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Delete project (soft delete, admin only)"""
    
    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}
