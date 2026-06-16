import os
from clerk_backend_api import Clerk
from fastapi import HTTPException, Depends, Header
from typing import Optional
from sqlalchemy.orm import Session

from models import get_db, OrganizationMember, User, Organization

clerk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

async def verify_jwt(token: str) -> dict:
    """Verify Clerk JWT and return user data"""
    try:
        decoded = clerk.verify_jwt(token)
        return decoded
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_user_from_clerk(user_id: str) -> dict:
    """Fetch user data from Clerk"""
    try:
        user = clerk.users.get(user_id)
        return user
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found")

async def get_current_user(
    authorization: str = Header(..., alias="Authorization")
) -> dict:
    """Get current user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    token = authorization.replace("Bearer ", "")
    user_data = await verify_jwt(token)
    return user_data

async def get_current_user_db(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token and return database User object"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    token = authorization.replace("Bearer ", "")
    user_data = await verify_jwt(token)
    
    # Get user from database
    clerk_user_id = user_data.get('sub')
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    
    if not user:
        # Auto-create user if not exists
        from models import Organization, OrganizationMember
        import uuid
        
        # Get user info from Clerk
        clerk_user = await get_user_from_clerk(clerk_user_id)
        
        # Create user
        user = User(
            clerk_user_id=clerk_user_id,
            email=clerk_user.get('email_addresses', [{}])[0].get('email_address') if clerk_user.get('email_addresses') else '',
            first_name=clerk_user.get('first_name'),
            last_name=clerk_user.get('last_name'),
            avatar_url=clerk_user.get('profile_image_url')
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create personal organization for user
        org_name = f"{user.first_name or 'User'}'s Organization" if user.first_name else "Personal Organization"
        org_slug = f"{user.email.split('@')[0]}-org" if user.email else f"user-{user.id}"
        
        org = Organization(
            name=org_name,
            slug=org_slug
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        
        # Add user as admin of their organization
        member = OrganizationMember(
            id=str(uuid.uuid4()),
            user_id=user.id,
            organization_id=org.id,
            role='admin',
            invited_by=user.id
        )
        db.add(member)
        db.commit()
    
    return user

def get_user_role_in_organization(user_id: str, organization_id: str, db: Session) -> str:
    """Get user's role in an organization"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.organization_id == organization_id
    ).first()
    
    if not member:
        return None  # User is not a member
    
    return member.role

def require_organization_role(required_roles: list[str]):
    """Dependency to require specific role(s) in organization"""
    async def role_dependency(
        organization_id: str,
        current_user: User = Depends(get_current_user_db),
        db: Session = Depends(get_db)
    ):
        user_role = get_user_role_in_organization(str(current_user.id), organization_id, db)
        
        if user_role is None:
            raise HTTPException(
                status_code=403, 
                detail="User is not a member of this organization"
            )
        
        if user_role not in required_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"User role '{user_role}' does not have required permissions. Required: {required_roles}"
            )
        
        return current_user
    return role_dependency

def require_role(required_role: str):
    """Dependency to require specific role (legacy - use require_organization_role)"""
    return require_organization_role([required_role])

def check_organization_access(user_id: str, organization_id: str, db: Session) -> bool:
    """Check if user has access to organization"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.organization_id == organization_id
    ).first()
    
    return member is not None

def check_project_access(user_id: str, project_id: str, db: Session) -> bool:
    """Check if user has access to project through organization membership"""
    from models import Project
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return False
    
    return check_organization_access(user_id, str(project.organization_id), db)
