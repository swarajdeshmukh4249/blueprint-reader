from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base
import uuid

class RateCard(Base):
    __tablename__ = "rate_cards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    effective_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    is_default = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RateCardItem(Base):
    __tablename__ = "rate_card_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rate_card_id = Column(UUID(as_uuid=True), ForeignKey("rate_cards.id", ondelete="CASCADE"), nullable=False)
    item_code = Column(String(100), nullable=True)
    category = Column(String(255), nullable=True)
    description = Column(String, nullable=False)
    unit = Column(String(50), nullable=False)
    rate = Column(Numeric(12, 2), nullable=False)
    material_cost = Column(Numeric(12, 2), nullable=True)
    labour_cost = Column(Numeric(12, 2), nullable=True)
    overhead_cost = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class MaterialRateHistory(Base):
    __tablename__ = "material_rate_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    rate = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(50), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
