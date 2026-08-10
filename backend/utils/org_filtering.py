"""
Organization-level data isolation utilities.
Ensures all endpoints verify user has access to the organization before returning data.
"""

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
import uuid as uuid_lib

from models import get_db, Organization, OrganizationMember, User, Project
from auth.clerk import get_current_user_db


def verify_user_org_access(
    user_id: UUID,
    organization_id: UUID,
    db: Session
) -> bool:
    """
    Verify that a user is a member of the specified organization.
    
    Args:
        user_id: User UUID to check
        organization_id: Organization UUID to verify access to
        db: Database session
        
    Returns:
        bool: True if user is a member, False otherwise
    """
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.organization_id == organization_id
    ).first()
    
    return membership is not None


def verify_user_project_access(
    user_id: UUID,
    project_id: UUID,
    db: Session
) -> bool:
    """
    Verify that a user has access to a project through organization membership.
    
    Args:
        user_id: User UUID to check
        project_id: Project UUID to verify access to
        db: Database session
        
    Returns:
        bool: True if user has access, False otherwise
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return False
    
    return verify_user_org_access(user_id, project.organization_id, db)


def get_user_organizations(
    user_id: UUID,
    db: Session
) -> list[UUID]:
    """
    Get all organization IDs that a user is a member of.
    
    Args:
        user_id: User UUID
        db: Database session
        
    Returns:
        list: List of organization UUIDs
    """
    memberships = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id
    ).all()
    
    return [m.organization_id for m in memberships]


def require_org_access(
    organization_id: str,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
) -> UUID:
    """
    Dependency that requires the current user to be a member of the specified organization.
    Raises HTTPException if user doesn't have access.
    
    Args:
        organization_id: Organization ID to verify (as string)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UUID: The organization ID (as UUID) if access is granted
        
    Raises:
        HTTPException: 400 if organization_id is invalid
        HTTPException: 403 if user doesn't have access to organization
    """
    try:
        org_uuid = uuid_lib.UUID(organization_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid organization_id format")
    
    if not verify_user_org_access(current_user.id, org_uuid, db):
        raise HTTPException(
            status_code=403,
            detail="User does not have access to this organization"
        )
    
    return org_uuid


def require_project_access(
    project_id: str,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
) -> UUID:
    """
    Dependency that requires the current user to have access to a project.
    
    Args:
        project_id: Project ID to verify (as string)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UUID: The project ID (as UUID) if access is granted
        
    Raises:
        HTTPException: 400 if project_id is invalid
        HTTPException: 404 if project doesn't exist
        HTTPException: 403 if user doesn't have access to project
    """
    try:
        project_uuid = uuid_lib.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id format")
    
    project = db.query(Project).filter(Project.id == project_uuid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not verify_user_project_access(current_user.id, project_uuid, db):
        raise HTTPException(
            status_code=403,
            detail="User does not have access to this project"
        )
    
    return project_uuid


def get_user_org_ids_query_filter(
    user_id: UUID,
    db: Session,
    model_org_id_column
):
    """
    Get a SQLAlchemy filter that restricts queries to user's organizations.
    
    Args:
        user_id: User UUID
        db: Database session
        model_org_id_column: SQLAlchemy column to filter (e.g., Project.organization_id)
        
    Returns:
        SQLAlchemy filter clause
    """
    user_org_ids = get_user_organizations(user_id, db)
    
    if not user_org_ids:
        # User has no organizations - return filter that matches nothing
        return model_org_id_column == None
    
    return model_org_id_column.in_(user_org_ids)
