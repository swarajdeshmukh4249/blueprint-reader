from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base
import uuid
import secrets

class PublicShare(Base):
    __tablename__ = "public_shares"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    share_token = Column(String(64), unique=True, nullable=False, index=True)
    blueprint_file_id = Column(UUID(as_uuid=True), ForeignKey("blueprint_files.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Share settings
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    password = Column(String(255), nullable=True)  # Optional password protection
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    
    # Access tracking
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token for sharing"""
        return secrets.token_urlsafe(32)
