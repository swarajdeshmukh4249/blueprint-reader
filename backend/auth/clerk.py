import os
from clerk_backend_api import Clerk
from fastapi import HTTPException, Depends, Header
from typing import Optional

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

def require_role(required_role: str):
    """Dependency to require specific role"""
    async def role_dependency(
        current_user: dict = Depends(get_current_user)
    ):
        # This would check the user's role in the organization
        # For now, we'll implement a basic version
        return current_user
    return role_dependency
