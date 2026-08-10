from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Numeric, Boolean, Text, CheckConstraint
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
    
    # ArchVision v2 additional fields
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    file_path = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_type = Column(String(20), nullable=True)
    progress = Column(Integer, default=0, nullable=True)
    current_stage = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_of_job_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        CheckConstraint('progress >= 0 AND progress <= 100', name='check_progress_range'),
        CheckConstraint("status IN ('queued', 'processing', 'completed', 'failed')", name='check_valid_status'),
        CheckConstraint("current_stage IN ('uploading', 'preparing', 'extracting', 'detecting', 'calibrating', 'calculating', 'estimating', 'finalizing')", name='check_valid_stage'),
    )

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
    is_user_corrected = Column(Boolean, default=False)  # ArchVision v2 field
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

# ArchVision v2: Dimensions table for extracted measurements
class Dimension(Base):
    __tablename__ = "dimensions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    value = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    blueprint_coordinates = Column(JSON, nullable=True)
    linked_room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)
    confidence = Column(Numeric(5, 2), default=0.0)
    is_user_corrected = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# ArchVision v2: Detected objects table for AI-detected elements
class DetectedObject(Base):
    __tablename__ = "detected_objects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    object_type = Column(String(50), nullable=False)
    geometry = Column(JSON, nullable=False)
    confidence = Column(Numeric(5, 2), default=0.0)
    properties = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("object_type IN ('wall', 'door', 'window', 'column', 'stair', 'furniture', 'other')", name='check_valid_object_type'),
    )

# ArchVision v2: Corrections table for audit trail
class Correction(Base):
    __tablename__ = "corrections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    target_table = Column(String(50), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    field = Column(String(100), nullable=False)
    original_value = Column(Text, nullable=True)
    corrected_value = Column(Text, nullable=False)
    corrected_at = Column(DateTime(timezone=True), server_default=func.now())
    corrected_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    correction_reason = Column(Text, nullable=True)
    properties = Column(JSON, default={})
    
    __table_args__ = (
        CheckConstraint("target_table IN ('rooms', 'dimensions', 'openings', 'detected_objects', 'boq_items')", name='check_valid_target_table'),
    )

# ArchVision v2: Analysis results summary table
class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Summary metrics
    total_floor_area = Column(Numeric(12, 2), nullable=True)
    room_count = Column(Integer, default=0)
    wall_length = Column(Numeric(12, 2), default=0)
    door_count = Column(Integer, default=0)
    window_count = Column(Integer, default=0)
    
    # Cost estimates
    estimated_material_cost = Column(Numeric(14, 2), default=0)
    estimated_total_cost = Column(Numeric(14, 2), default=0)
    
    # Quality metrics
    confidence_score = Column(Numeric(5, 2), default=0)
    
    # Scale calibration data
    scale_calibration = Column(JSON, default={})
    
    # Processing metadata
    processing_metadata = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
