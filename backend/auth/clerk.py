import os
import logging
from clerk_backend_api import Clerk
from clerk_backend_api.security import verify_token
from clerk_backend_api.security.types import VerifyTokenOptions
from fastapi import HTTPException, Depends, Header
from typing import Optional
from sqlalchemy.orm import Session

from models import get_db, OrganizationMember, User, Organization

logger = logging.getLogger(__name__)

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_JWT_KEY = os.getenv("CLERK_JWT_KEY")  # optional PEM for networkless verify

clerk = Clerk(bearer_auth=CLERK_SECRET_KEY)

# Optional azp allow-list. Leave unset unless CLERK_AUTHORIZED_PARTIES is configured,
# so local/dev hosts don't get false "Invalid token" failures.
_AUTHORIZED_PARTIES = None
_raw_parties = os.getenv("CLERK_AUTHORIZED_PARTIES")
if _raw_parties:
    _AUTHORIZED_PARTIES = [origin.strip() for origin in _raw_parties.split(",") if origin.strip()]


async def verify_jwt(token: str) -> dict:
    """Verify Clerk session JWT and return claims (includes `sub` user id)."""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")

    if not CLERK_SECRET_KEY and not CLERK_JWT_KEY:
        logger.error("CLERK_SECRET_KEY / CLERK_JWT_KEY not configured")
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        options = VerifyTokenOptions(
            secret_key=CLERK_SECRET_KEY if not CLERK_JWT_KEY else None,
            jwt_key=CLERK_JWT_KEY,
            authorized_parties=_AUTHORIZED_PARTIES,
        )
        decoded = verify_token(token, options)
        logger.debug("Token verified successfully for user: %s", decoded.get("sub"))
        return decoded
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token verification failed: %s: %s", type(e).__name__, e)
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_user_from_clerk(user_id: str) -> dict:
    """Fetch user data from Clerk"""
    try:
        user = clerk.users.get(user_id=user_id)
        # Normalize SDK response to a plain dict the rest of the app expects
        if hasattr(user, "model_dump"):
            return user.model_dump()
        if hasattr(user, "dict"):
            return user.dict()
        if isinstance(user, dict):
            return user
        # Fallback: attribute access used by get_current_user_db
        email_addresses = getattr(user, "email_addresses", None) or []
        emails = []
        for e in email_addresses:
            if isinstance(e, dict):
                emails.append(e)
            else:
                emails.append({
                    "email_address": getattr(e, "email_address", None),
                })
        return {
            "email_addresses": emails,
            "first_name": getattr(user, "first_name", None),
            "last_name": getattr(user, "last_name", None),
            "profile_image_url": getattr(user, "image_url", None) or getattr(user, "profile_image_url", None),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch Clerk user %s: %s", user_id, e)
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


async def get_current_user_with_org(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> tuple:
    """Get current user and their organizations from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    token = authorization.replace("Bearer ", "")
    user_data = await verify_jwt(token)
    
    # Get user from database to get org memberships
    clerk_user_id = user_data.get('sub')
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found in database")
    
    # Get user's organizations
    org_memberships = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user.id
    ).all()
    
    org_ids = [str(m.organization_id) for m in org_memberships]
    
    return user_data, org_ids

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
    
    import uuid

    def _ensure_personal_org(existing_user: User) -> None:
        """Attach user to a personal org, reusing an existing slug when present."""
        membership = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == existing_user.id
        ).first()
        if membership:
            return

        org_name = (
            f"{existing_user.first_name or 'User'}'s Organization"
            if existing_user.first_name
            else "Personal Organization"
        )
        base_slug = (
            f"{existing_user.email.split('@')[0]}-org"
            if existing_user.email
            else f"user-{existing_user.id}"
        )

        org = db.query(Organization).filter(Organization.slug == base_slug).first()
        if not org:
            slug = base_slug
            # If somehow slug is taken between check and insert, use a unique fallback.
            if db.query(Organization).filter(Organization.slug == slug).first():
                slug = f"{base_slug}-{str(existing_user.id)[:8]}"
            org = Organization(name=org_name, slug=slug)
            db.add(org)
            db.commit()
            db.refresh(org)

        member = OrganizationMember(
            id=uuid.uuid4(),
            user_id=existing_user.id,
            organization_id=org.id,
            role='admin',
            invited_by=existing_user.id,
        )
        db.add(member)
        db.commit()

    if not user:
        # Auto-create user if not exists
        clerk_user = await get_user_from_clerk(clerk_user_id)

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
        _ensure_personal_org(user)
    else:
        _ensure_personal_org(user)

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
