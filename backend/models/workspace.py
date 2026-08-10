from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base
import uuid

class DashboardPreference(Base):
    """Store user dashboard customization preferences per organization"""
    __tablename__ = "dashboard_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Widget configuration: which widgets to show and in what order
    # Example: {"widgets": [{"id": "kpi", "position": 0, "enabled": true}, ...]}
    widget_config = Column(JSON, default={"widgets": []})
    
    # Filter preferences: default filters to apply to dashboard
    # Example: {"status_filter": "active", "date_range": "last_30_days"}
    filter_preferences = Column(JSON, default={})
    
    # View preferences: layout, theme, etc.
    # Example: {"layout": "grid", "theme": "light", "rows_per_page": 10}
    view_preferences = Column(JSON, default={"layout": "grid", "theme": "light", "rows_per_page": 10})
    
    # Saved reports or views
    # Example: [{"id": "report1", "name": "Q1 Analysis", "filters": {...}}]
    saved_views = Column(JSON, default=[])
    
    # Default dashboard to show when switching to this organization
    default_dashboard = Column(String(100), default="executive")  # executive, analytics, project, etc.
    
    # Refresh interval in seconds (0 = manual refresh)
    refresh_interval = Column(Integer, default=300)
    
    # Last accessed time for this org
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WorkspaceContext(Base):
    """Track user's current workspace context for quick switching"""
    __tablename__ = "workspace_contexts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Current active organization
    current_organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Last accessed organizations (for quick access switcher)
    # Store as JSON: [{"org_id": "...", "accessed_at": "..."}]
    recent_organizations = Column(JSON, default=[])
    
    # Favorite organizations for quick access
    favorite_organization_ids = Column(JSON, default=[])
    
    # Last current project in the organization
    current_project_id = Column(UUID(as_uuid=True), nullable=True)
    
    # User's preferred timezone
    timezone = Column(String(50), default="UTC")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserNotificationPreference(Base):
    """User notification preferences per organization"""
    __tablename__ = "user_notification_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Enable notifications: email, in-app, push
    email_notifications_enabled = Column(Boolean, default=True)
    in_app_notifications_enabled = Column(Boolean, default=True)
    push_notifications_enabled = Column(Boolean, default=True)
    
    # Notification types
    notify_on_analysis_complete = Column(Boolean, default=True)
    notify_on_approval_needed = Column(Boolean, default=True)
    notify_on_team_comment = Column(Boolean, default=True)
    notify_on_project_shared = Column(Boolean, default=True)
    notify_on_cost_update = Column(Boolean, default=True)
    
    # Notification frequency
    notification_frequency = Column(String(50), default="immediate")  # immediate, daily, weekly
    
    # Quiet hours (no notifications between these times)
    quiet_hours_start = Column(String(5), nullable=True)  # "22:00"
    quiet_hours_end = Column(String(5), nullable=True)    # "08:00"
    quiet_hours_enabled = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
