from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Numeric, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base
import uuid
import enum

class DiffStatus(str, enum.Enum):
    MATCH = "match"
    CHANGED = "changed"
    ADDED = "added"
    REMOVED = "removed"

class FloorComparison(Base):
    __tablename__ = "floor_comparisons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    floor_a_id = Column(UUID(as_uuid=True), nullable=True)
    floor_b_id = Column(UUID(as_uuid=True), nullable=True)
    floor_a_label = Column(String(100), nullable=True)
    floor_b_label = Column(String(100), nullable=True)
    
    # Summary stats
    total_area_a = Column(Numeric(12, 2), nullable=True)
    total_area_b = Column(Numeric(12, 2), nullable=True)
    area_delta = Column(Numeric(12, 2), nullable=True)
    boq_cost_a = Column(Numeric(15, 2), nullable=True)
    boq_cost_b = Column(Numeric(15, 2), nullable=True)
    cost_delta = Column(Numeric(15, 2), nullable=True)
    
    # Room diffs stored as JSON
    room_diffs = Column(JSON, nullable=True)
    
    # Metadata
    comparison_type = Column(String(50), default='floor')  # 'floor', 'version', etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)
