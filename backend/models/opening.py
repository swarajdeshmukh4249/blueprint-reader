from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import Boolean
from .base import Base
import uuid

class Opening(Base):
    __tablename__ = "openings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=True)
    analysis_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    opening_type = Column(String(50), nullable=False)
    width_ft = Column(Numeric(10, 2), nullable=True)
    height_ft = Column(Numeric(10, 2), nullable=True)
    width_m = Column(Numeric(10, 2), nullable=True)
    height_m = Column(Numeric(10, 2), nullable=True)
    position_x = Column(Numeric(12, 2), nullable=True)
    position_y = Column(Numeric(12, 2), nullable=True)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    is_user_corrected = Column(Boolean, default=False)  # ArchVision v2 field
    created_at = Column(DateTime(timezone=True), server_default=func.now())