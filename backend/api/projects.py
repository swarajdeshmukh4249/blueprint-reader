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
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    
    # Optional authentication
    current_user = None
    if authorization:
        try:
            current_user = verify_jwt(authorization.replace("Bearer ", ""))
        except Exception as e:
            print(f"Auth failed: {e}")
            pass  # Allow request to proceed even if auth fails
    
    # Verify organization exists if provided
    org_uuid = None
    if project.organization_id:
        try:
            org = db.query(Organization).filter(Organization.id == uuid.UUID(project.organization_id)).first()
            if not org:
                raise HTTPException(status_code=404, detail="Organization not found")
            org_uuid = uuid.UUID(project.organization_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid organization_id format")
    
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
        created_by=current_user.get('sub') if current_user else None
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
    limit: int = Query(5, ge=1, le=100),
    sort: str = Query("updated_at:desc", pattern="^[a-z_]+:(asc|desc)$"),
    organization_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """List projects for dashboard with limit and sort"""
    
    # Optional authentication
    current_user = None
    if authorization:
        try:
            current_user = verify_jwt(authorization.replace("Bearer ", ""))
        except Exception as e:
            print(f"Auth failed: {e}")
            pass  # Allow request to proceed even if auth fails
    
    query = db.query(Project)
    
    # Filter by user's organizations if authenticated
    if current_user:
        clerk_user_id = current_user.get('sub')
        if clerk_user_id:
            # Get user from database
            user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
            if user:
                # Get user's organization memberships
                from models import OrganizationMember
                user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).all()]
                
                # Filter projects by user's organizations
                if user_org_ids:
                    # If organization_id provided, verify user has access
                    if organization_id:
                        if uuid.UUID(organization_id) not in user_org_ids:
                            raise HTTPException(status_code=403, detail="Access denied to this organization")
                        query = query.filter(Project.organization_id == uuid.UUID(organization_id))
                    else:
                        query = query.filter(Project.organization_id.in_(user_org_ids))
                else:
                    # User has no organization memberships, return empty
                    query = query.filter(False)
        else:
            # No clerk_user_id in token, deny access
            raise HTTPException(status_code=401, detail="Authentication required")
    else:
        # No authenticated user, deny access
        raise HTTPException(status_code=401, detail="Authentication required")
    
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
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get project by ID"""
    
    # Get current user
    current_user = None
    if authorization:
        try:
            current_user = verify_jwt(authorization.replace("Bearer ", ""))
        except Exception as e:
            print(f"Auth failed: {e}")
            pass  # Allow request to proceed even if auth fails
    
    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check user has access to the project
    if current_user:
        clerk_user_id = current_user.get('sub')
        if clerk_user_id:
            user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
            if user:
                user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).all()]
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
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Update project"""
    
    # Get current user
    current_user = None
    if authorization:
        try:
            current_user = verify_jwt(authorization.replace("Bearer ", ""))
        except Exception as e:
            print(f"Auth failed: {e}")
            pass  # Allow request to proceed even if auth fails
    
    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check user has access to the project
    if current_user:
        clerk_user_id = current_user.get('sub')
        if clerk_user_id:
            user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
            if user:
                user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).all()]
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
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Delete project (soft delete)"""
    
    # Get current user
    current_user = None
    if authorization:
        try:
            current_user = verify_jwt(authorization.replace("Bearer ", ""))
        except Exception as e:
            print(f"Auth failed: {e}")
            pass  # Allow request to proceed even if auth fails
    
    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check user has access to the project
    if current_user:
        clerk_user_id = current_user.get('sub')
        if clerk_user_id:
            user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
            if user:
                user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).all()]
                if project.organization_id not in user_org_ids:
                    raise HTTPException(status_code=403, detail="Access denied to this project")
    
    project.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}
