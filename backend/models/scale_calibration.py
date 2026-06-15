from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base
import uuid

class ScaleCalibration(Base):
    __tablename__ = "scale_calibrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    point1_x = Column(Numeric(12, 2), nullable=True)
    point1_y = Column(Numeric(12, 2), nullable=True)
    point2_x = Column(Numeric(12, 2), nullable=True)
    point2_y = Column(Numeric(12, 2), nullable=True)
    known_distance = Column(Numeric(12, 2), nullable=False)
    known_unit = Column(String(20), nullable=False)
    calculated_scale = Column(Numeric(12, 6), nullable=True)
    reference_type = Column(String(50), nullable=True)
    
    # Confidence fields
    confidence_score = Column(Numeric(5, 3), nullable=True)
    confidence_level = Column(String(20), nullable=True)
    confidence_badge = Column(JSON, nullable=True)
    confidence_warnings = Column(JSON, nullable=True)
    confidence_factors = Column(JSON, nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
