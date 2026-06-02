from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base
import uuid

class CostBenchmark(Base):
    __tablename__ = "cost_benchmarks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Benchmark category
    category = Column(String(100), nullable=False)  # e.g., "cost_per_sqft", "material_usage", "construction_time"
    metric_name = Column(String(255), nullable=False)  # e.g., "Steel Usage", "Cement Usage"
    
    # Your project values
    your_value = Column(Float, nullable=False)
    your_unit = Column(String(50), nullable=True)  # e.g., "sq ft", "kg/sq ft", "days"
    
    # Industry benchmark values
    benchmark_value = Column(Float, nullable=False)
    benchmark_unit = Column(String(50), nullable=True)
    benchmark_source = Column(String(255), nullable=True)  # e.g., "DSR 2023", "Industry Average"
    
    # Variance analysis
    variance_percentage = Column(Float, nullable=True)  # (your_value - benchmark_value) / benchmark_value * 100
    variance_status = Column(String(20), nullable=True)  # "above", "below", "within_range"
    
    # Context
    region = Column(String(100), nullable=True)
    building_type = Column(String(100), nullable=True)
    project_size_category = Column(String(50), nullable=True)  # "small", "medium", "large"
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class IndustryCostData(Base):
    __tablename__ = "industry_cost_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Classification
    category = Column(String(100), nullable=False, index=True)
    metric_name = Column(String(255), nullable=False)
    
    # Benchmark values
    benchmark_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)
    
    # Ranges
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    percentile_25 = Column(Float, nullable=True)
    percentile_75 = Column(Float, nullable=True)
    
    # Context
    region = Column(String(100), nullable=True, index=True)
    building_type = Column(String(100), nullable=True, index=True)
    project_size = Column(String(50), nullable=True)  # "small", "medium", "large"
    
    # Source
    source = Column(String(255), nullable=True)  # e.g., "DSR 2023", "Industry Survey"
    source_year = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
