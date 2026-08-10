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
    organization_id: Optional[str] = None
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
    organization_id: Optional[str]
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
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Create a new project (requires authentication). The project will be created under the user's organization if organization_id is not provided."""

    # Determine organization: prefer provided organization_id, otherwise use user's personal/org membership
    org_uuid = None
    if project.organization_id:
        try:
            org = db.query(Organization).filter(Organization.id == uuid.UUID(project.organization_id)).first()
            if not org:
                raise HTTPException(status_code=404, detail="Organization not found")
            # Verify user is member of the organization
            from models import OrganizationMember
            membership = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == current_user.id
            ).first()
            if not membership:
                raise HTTPException(status_code=403, detail="User is not a member of the specified organization")
            org_uuid = uuid.UUID(project.organization_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid organization_id format")
    else:
        # Use the first organization the user is a member of (get personal org created by get_current_user_db)
        from models import OrganizationMember
        member = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).first()
        if member:
            org_uuid = member.organization_id
        else:
            # Auto-create a personal organization for the user if they don't have one
            personal_org = Organization(
                name=f"{current_user.first_name or current_user.email.split('@')[0]}'s Workspace",
                slug=f"workspace-{current_user.id[:8]}",
                plan_tier='starter',
                max_users=5,
                max_projects=10,
                max_storage_gb=10
            )
            db.add(personal_org)
            db.commit()
            db.refresh(personal_org)
            
            # Add user as admin of their personal organization
            org_member = OrganizationMember(
                organization_id=personal_org.id,
                user_id=current_user.id,
                role='admin'
            )
            db.add(org_member)
            db.commit()
            
            org_uuid = personal_org.id

    # Create project
    new_project = Project(
        organization_id=org_uuid,
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
        organization_id=str(new_project.organization_id) if new_project.organization_id else None,
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
    limit: int = Query(50, ge=1, le=100),
    sort: str = Query("created_at:desc", pattern="^[a-z_]+:(asc|desc)$"),
    organization_id: Optional[str] = None,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """List projects for dashboard with limit and sort. Requires authentication and returns projects scoped to the user's organizations."""

    query = db.query(Project)

    # Get user's organization memberships
    from models import OrganizationMember
    user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).all()]

    # Filter projects by user's organizations
    if user_org_ids:
        query = query.filter(Project.organization_id.in_(user_org_ids))
    else:
        return []

    # Filter by organization if provided (additional filter)
    if organization_id:
        query = query.filter(Project.organization_id == uuid.UUID(organization_id))
    
    # Parse sort parameter
    sort_field, sort_direction = sort.split(":")
    # Prefer created_at — updated_at is often NULL for newly created projects
    if sort_field == "updated_at":
        primary = Project.updated_at
        secondary = Project.created_at
    else:
        primary = Project.created_at
        secondary = Project.updated_at

    if sort_direction == "desc":
        query = query.order_by(primary.desc().nullslast(), secondary.desc().nullslast())
    else:
        query = query.order_by(primary.asc().nullslast(), secondary.asc().nullslast())
    
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
        
        status = p.status or "in_progress"
        
        # Check if any analysis failed
        failed_analysis = db.query(AnalysisVersion).filter(
            AnalysisVersion.project_id == p.id,
            AnalysisVersion.status == "failed"
        ).first()
        
        if failed_analysis:
            status = "failed"
        elif floor_count > 0 and analysis_count == floor_count:
            from config import CONFIDENCE_MEDIUM
            analyses = db.query(AnalysisVersion).filter(
                AnalysisVersion.project_id == p.id
            ).all()
            
            has_low_confidence = False
            for analysis in analyses:
                analysis_payload = getattr(analysis, "raw_result", None) or {}
                rooms = analysis_payload.get("rooms", []) if isinstance(analysis_payload, dict) else []
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
        
        estimated_cost = None
        
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
    """Get project by ID (requires authentication)"""

    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check user has access to the project
    from models import OrganizationMember
    user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).all()]
    if project.organization_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Access denied to this project")
    
    return ProjectDetailResponse(
        id=str(project.id),
        organization_id=str(project.organization_id) if project.organization_id else None,
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
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Update project (requires authentication)"""

    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check user has access to the project
    from models import OrganizationMember
    user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).all()]
    if project.organization_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Access denied to this project")
    
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
        organization_id=str(project.organization_id) if project.organization_id else None,
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
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Delete project (soft delete) (requires authentication)"""

    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check user has access to the project
    from models import OrganizationMember
    user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).all()]
    if project.organization_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="Access denied to this project")

    project.deleted_at = datetime.utcnow()
    db.commit()

    return {"success": True}
