from sqlalchemy import Column, String, DateTime, Integer, Numeric, UUID, ForeignKey, Date, UniqueConstraint
from sqlalchemy.sql import func
from .base import Base
import uuid


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    period_type = Column(String(20), nullable=False)
    
    total_projects = Column(Integer, default=0)
    active_projects = Column(Integer, default=0)
    completed_projects = Column(Integer, default=0)
    total_floor_area_sqft = Column(Numeric(15, 2), default=0)
    total_boq_value = Column(Numeric(18, 2), default=0)
    avg_cost_per_sqft = Column(Numeric(12, 2), default=0)
    avg_project_cost = Column(Numeric(18, 2), default=0)
    
    projects_trend = Column(Numeric(5, 2), default=0)
    boq_value_trend = Column(Numeric(5, 2), default=0)
    cost_per_sqft_trend = Column(Numeric(5, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (UniqueConstraint('organization_id', 'snapshot_date', 'period_type', name='uq_analytics_snapshot'),)


class CostTrend(Base):
    __tablename__ = "cost_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    record_date = Column(Date, nullable=False)
    
    total_cost = Column(Numeric(18, 2), default=0)
    material_cost = Column(Numeric(18, 2), default=0)
    labour_cost = Column(Numeric(18, 2), default=0)
    overhead_cost = Column(Numeric(18, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CostBreakdown(Base):
    __tablename__ = "cost_breakdown"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    analysis_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id"))
    
    category = Column(String(100), nullable=False)
    cost = Column(Numeric(18, 2), default=0)
    percentage = Column(Numeric(5, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MaterialStatistic(Base):
    __tablename__ = "material_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    
    material_name = Column(String(100), nullable=False)
    quantity = Column(Numeric(15, 3), default=0)
    unit = Column(String(50), nullable=False)
    cost = Column(Numeric(18, 2), default=0)
    
    record_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MaterialCostBreakdown(Base):
    __tablename__ = "material_cost_breakdown"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    
    material_name = Column(String(100), nullable=False)
    cost = Column(Numeric(18, 2), default=0)
    quantity = Column(Numeric(15, 3), default=0)
    cost_per_unit = Column(Numeric(12, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RegionalCostRate(Base):
    __tablename__ = "regional_cost_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    country = Column(String(100), nullable=False)
    state = Column(String(100))
    city = Column(String(100), nullable=False)
    
    material_name = Column(String(100), nullable=False)
    current_rate = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(50), nullable=False)
    
    trend = Column(String(20), default='stable')
    trend_percentage = Column(Numeric(5, 2), default=0)
    
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RegionalCostHistory(Base):
    __tablename__ = "regional_cost_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regional_rate_id = Column(UUID(as_uuid=True), ForeignKey("regional_cost_rates.id"))
    
    rate = Column(Numeric(12, 2), nullable=False)
    record_date = Column(Date, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AIQualityMetric(Base):
    __tablename__ = "ai_quality_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    analysis_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id"))
    
    total_rooms_detected = Column(Integer, default=0)
    high_confidence_rooms = Column(Integer, default=0)
    medium_confidence_rooms = Column(Integer, default=0)
    low_confidence_rooms = Column(Integer, default=0)
    
    rooms_corrected = Column(Integer, default=0)
    manual_corrections = Column(Integer, default=0)
    accuracy_rate = Column(Numeric(5, 2), default=0)
    
    avg_confidence_score = Column(Numeric(5, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RoomTypeCorrectionStat(Base):
    __tablename__ = "room_type_correction_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    room_type = Column(String(100), nullable=False)
    total_detections = Column(Integer, default=0)
    total_corrections = Column(Integer, default=0)
    correction_rate = Column(Numeric(5, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RevisionAnalytic(Base):
    __tablename__ = "revision_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    
    from_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id"))
    to_version_id = Column(UUID(as_uuid=True), ForeignKey("analysis_versions.id"))
    
    area_change_sqft = Column(Numeric(15, 2), default=0)
    boq_change = Column(Numeric(18, 2), default=0)
    cost_change = Column(Numeric(18, 2), default=0)
    
    rooms_added = Column(Integer, default=0)
    rooms_deleted = Column(Integer, default=0)
    rooms_modified = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TeamActivityMetric(Base):
    __tablename__ = "team_activity_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    activity_date = Column(Date, nullable=False)
    
    analyses_run = Column(Integer, default=0)
    reports_exported = Column(Integer, default=0)
    comments_added = Column(Integer, default=0)
    corrections_made = Column(Integer, default=0)
    approvals_given = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (UniqueConstraint('organization_id', 'user_id', 'activity_date', name='uq_team_activity'),)


class PortfolioAnalytic(Base):
    __tablename__ = "portfolio_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    total_portfolio_value = Column(Numeric(18, 2), default=0)
    total_area_sqft = Column(Numeric(15, 2), default=0)
    total_buildings = Column(Integer, default=0)
    total_floors = Column(Integer, default=0)
    
    residential_count = Column(Integer, default=0)
    commercial_count = Column(Integer, default=0)
    industrial_count = Column(Integer, default=0)
    mixed_use_count = Column(Integer, default=0)
    
    snapshot_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (UniqueConstraint('organization_id', 'snapshot_date', name='uq_portfolio_analytics'),)


class ApprovalAnalytic(Base):
    __tablename__ = "approval_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    snapshot_date = Column(Date, nullable=False)
    
    pending_approvals = Column(Integer, default=0)
    approved_reports = Column(Integer, default=0)
    rejected_reports = Column(Integer, default=0)
    avg_approval_time_hours = Column(Numeric(10, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (UniqueConstraint('organization_id', 'snapshot_date', name='uq_approval_analytics'),)


class BenchmarkingData(Base):
    __tablename__ = "benchmarking_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    
    benchmark_type = Column(String(50), nullable=False)
    benchmark_name = Column(String(100), nullable=False)
    
    project_value = Column(Numeric(18, 2), default=0)
    benchmark_value = Column(Numeric(18, 2), default=0)
    variance_percentage = Column(Numeric(5, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
