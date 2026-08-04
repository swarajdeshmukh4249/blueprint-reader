from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from models import get_db, Organization, User, OrganizationMember
from auth.clerk import get_current_user, verify_jwt, get_current_user_db, require_organization_role

router = APIRouter(prefix="/organizations", tags=["organizations"])

class OrganizationCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    logo_url: Optional[str] = None
    brand_color: Optional[str] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    brand_color: Optional[str] = None
    settings: Optional[dict] = None

class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    logo_url: Optional[str]
    brand_color: Optional[str]
    plan_tier: str
    max_users: int
    max_projects: int
    max_storage_gb: int
    created_at: datetime

@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org: OrganizationCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Create a new organization"""
    
    # Get current user
    user = None
    if authorization:
        try:
            token = authorization.replace("Bearer ", "")
            user_data = await verify_jwt(token)
            # Get user from database
            from models import User
            clerk_user_id = user_data.get('sub')
            user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
        except Exception:
            pass
    
    # Auto-generate slug if not provided
    slug = org.slug
    if not slug:
        slug = org.name.lower().replace(' ', '-').replace('_', '-')
    
    # Check if slug is available
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already taken")
    
    # Create organization
    new_org = Organization(
        name=org.name,
        slug=slug,
        logo_url=org.logo_url,
        brand_color=org.brand_color
    )
    
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    
    # Add creator as admin
    if user:
        member = OrganizationMember(
            organization_id=new_org.id,
            user_id=user.id,
            role='admin',
            invited_by=user.id
        )
        db.add(member)
        db.commit()
    
    return OrganizationResponse(
        id=str(new_org.id),
        name=new_org.name,
        slug=new_org.slug,
        logo_url=new_org.logo_url,
        brand_color=new_org.brand_color,
        plan_tier=new_org.plan_tier,
        max_users=new_org.max_users,
        max_projects=new_org.max_projects,
        max_storage_gb=new_org.max_storage_gb,
        created_at=new_org.created_at
    )

@router.get("/", response_model=list[OrganizationResponse])
async def list_organizations(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """List organizations for current user"""
    
    # Get current user
    user = None
    if authorization:
        try:
            token = authorization.replace("Bearer ", "")
            user_data = await verify_jwt(token)
            # Get user from database
            clerk_user_id = user_data.get('sub')
            user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
        except Exception:
            pass  # Allow request to proceed even if auth fails
    
    # Filter by user's memberships if authenticated
    if user:
        user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).all()]
        organizations = db.query(Organization).filter(Organization.id.in_(user_org_ids)).all()
    else:
        # No authenticated user, return all organizations for demo
        organizations = db.query(Organization).all()
    
    return [
        OrganizationResponse(
            id=str(org.id),
            name=org.name,
            slug=org.slug,
            logo_url=org.logo_url,
            brand_color=org.brand_color,
            plan_tier=org.plan_tier,
            max_users=org.max_users,
            max_projects=org.max_projects,
            max_storage_gb=org.max_storage_gb,
            created_at=org.created_at
        )
        for org in organizations
    ]

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get organization by ID"""
    
    org = db.query(Organization).filter(Organization.id == uuid.UUID(org_id)).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check user has access to this organization
    
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        logo_url=org.logo_url,
        brand_color=org.brand_color,
        plan_tier=org.plan_tier,
        max_users=org.max_users,
        max_projects=org.max_projects,
        max_storage_gb=org.max_storage_gb,
        created_at=org.created_at
    )

@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    org_update: OrganizationUpdate,
    current_user: User = Depends(require_organization_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Update organization (admin only)"""
    
    org = db.query(Organization).filter(Organization.id == uuid.UUID(org_id)).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if org_update.name is not None:
        org.name = org_update.name
    if org_update.logo_url is not None:
        org.logo_url = org_update.logo_url
    if org_update.brand_color is not None:
        org.brand_color = org_update.brand_color
    if org_update.settings is not None:
        org.settings = org_update.settings
    
    org.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(org)
    
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        logo_url=org.logo_url,
        brand_color=org.brand_color,
        plan_tier=org.plan_tier,
        max_users=org.max_users,
        max_projects=org.max_projects,
        max_storage_gb=org.max_storage_gb,
        created_at=org.created_at
    )
