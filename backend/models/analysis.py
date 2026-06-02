from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base
import uuid

class AnalysisVersion(Base):
    __tablename__ = "analysis_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    blueprint_file_id = Column(UUID(as_uuid=True), nullable=True)
    version_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=True)
    description = Column(String, nullable=True)
    status = Column(String(50), default='processing', index=True)
    total_area_sqft = Column(Numeric(12, 2), nullable=True)
    total_area_sqm = Column(Numeric(12, 2), nullable=True)
    room_count = Column(Integer, nullable=True)
    floor_count = Column(Integer, nullable=True)
    door_count = Column(Integer, nullable=True)
    window_count = Column(Integer, nullable=True)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    ai_model_used = Column(String(100), nullable=True)
    settings = Column(JSON, default={})
    raw_result = Column(JSON, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    room_type = Column(String(100), nullable=True)
    floor_number = Column(Integer, default=1)
    area_sqft = Column(Numeric(12, 2), nullable=True)
    area_sqm = Column(Numeric(12, 2), nullable=True)
    width_ft = Column(Numeric(10, 2), nullable=True)
    height_ft = Column(Numeric(10, 2), nullable=True)
    width_m = Column(Numeric(10, 2), nullable=True)
    height_m = Column(Numeric(10, 2), nullable=True)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    source = Column(String(50), nullable=True)
    polygon_coordinates = Column(JSON, nullable=True)
    centroid_x = Column(Numeric(12, 2), nullable=True)
    centroid_y = Column(Numeric(12, 2), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BOQItem(Base):
    __tablename__ = "boq_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(255), nullable=False)
    item_code = Column(String(100), nullable=True)
    description = Column(String, nullable=False)
    unit = Column(String(50), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=True)
    rate = Column(Numeric(12, 2), nullable=True)
    amount = Column(Numeric(14, 2), nullable=True)
    source = Column(String(50), nullable=True)
    rate_card_id = Column(UUID(as_uuid=True), ForeignKey("rate_cards.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
