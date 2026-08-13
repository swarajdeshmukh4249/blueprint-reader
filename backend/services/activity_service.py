"""
Activity Feed Service
Tracks and retrieves activity events
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session
from models import Project, AnalysisVersion, BlueprintFile, Organization


class ActivityService:
    """Manages activity feed tracking and retrieval"""
    
    EVENT_TYPES = {
        "boq_generated": {"color": "green", "icon": "check"},
        "rooms_flagged": {"color": "amber", "icon": "alert"},
        "file_uploaded": {"color": "blue", "icon": "upload"},
        "boq_exported": {"color": "green", "icon": "download"},
        "calibration_applied": {"color": "red", "icon": "ruler"},
        "team_member_joined": {"color": "blue", "icon": "user"},
        "analysis_failed": {"color": "red", "icon": "x"},
    }
    
    def __init__(self, db: Session):
        """Initialize the activity service"""
        self.db = db
    
    def track_event(
        self,
        event_type: str,
        description: str,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track an activity event
        
        Args:
            event_type: Type of event
            description: Human-readable description
            project_id: Optional project ID
            user_id: Optional user ID
            metadata: Optional additional metadata
            
        Returns:
            Created activity event
        """
        event = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "description": description,
            "project_id": project_id,
            "user_id": user_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        # In production, this would be saved to a database table
        # For now, we'll return the event object
        return event
    
    def get_activities(
        self,
        limit: int = 10,
        project_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        organization_ids: Optional[List[uuid.UUID]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent activities synthesized from blueprint files and analyses.
        Always scoped to organization_ids / organization_id when provided.
        """
        activities: List[Dict[str, Any]] = []

        org_uuids: List[uuid.UUID] = []
        if organization_ids:
            org_uuids = list(organization_ids)
        elif organization_id:
            try:
                org_uuids = [uuid.UUID(organization_id)]
            except ValueError:
                return []

        # No org scope → nothing (callers must pass user orgs)
        if not org_uuids and not project_id:
            return []

        files_query = self.db.query(BlueprintFile).join(
            Project, BlueprintFile.project_id == Project.id, isouter=True
        )
        analyses_query = self.db.query(AnalysisVersion).join(
            Project, AnalysisVersion.project_id == Project.id
        )

        if project_id:
            try:
                project_uuid = uuid.UUID(project_id)
            except ValueError:
                return []
            files_query = files_query.filter(BlueprintFile.project_id == project_uuid)
            analyses_query = analyses_query.filter(AnalysisVersion.project_id == project_uuid)
            if org_uuids:
                files_query = files_query.filter(Project.organization_id.in_(org_uuids))
                analyses_query = analyses_query.filter(Project.organization_id.in_(org_uuids))
        else:
            files_query = files_query.filter(Project.organization_id.in_(org_uuids))
            analyses_query = analyses_query.filter(Project.organization_id.in_(org_uuids))

        files = files_query.order_by(BlueprintFile.created_at.desc()).limit(limit).all()
        for file in files:
            file_label = getattr(file, "filename", None) or getattr(file, "name", None) or "blueprint"
            activities.append({
                "id": str(uuid.uuid4()),
                "event_type": "file_uploaded",
                "description": f"New blueprint uploaded — {file_label}",
                "project_id": str(file.project_id) if file.project_id else None,
                "user_id": None,
                "metadata": {"file_id": str(file.id)},
                "created_at": file.created_at.isoformat() if file.created_at else datetime.utcnow().isoformat()
            })

        analyses = analyses_query.order_by(AnalysisVersion.created_at.desc()).limit(limit).all()
        for analysis in analyses:
            if analysis.status == "completed":
                activities.append({
                    "id": str(uuid.uuid4()),
                    "event_type": "boq_generated",
                    "description": "Analysis completed / BOQ generated",
                    "project_id": str(analysis.project_id),
                    "user_id": None,
                    "metadata": {"analysis_id": str(analysis.id)},
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else datetime.utcnow().isoformat()
                })
            elif analysis.status == "failed":
                activities.append({
                    "id": str(uuid.uuid4()),
                    "event_type": "analysis_failed",
                    "description": "Analysis failed for project",
                    "project_id": str(analysis.project_id),
                    "user_id": None,
                    "metadata": {"analysis_id": str(analysis.id)},
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else datetime.utcnow().isoformat()
                })

        activities.sort(key=lambda x: x["created_at"], reverse=True)
        activities = activities[:limit]

        for activity in activities:
            activity["formatted_time"] = self._format_timestamp(activity["created_at"])
            activity["event_info"] = self.EVENT_TYPES.get(
                activity["event_type"],
                {"color": "gray", "icon": "info"}
            )

        return activities
    
    def _format_timestamp(self, timestamp: str) -> str:
        """
        Format timestamp for display
        
        Args:
            timestamp: ISO8601 timestamp string
            
        Returns:
            Formatted time string
        """
        try:
            dt = datetime.fromisoformat(timestamp)
            now = datetime.utcnow()
            delta = now - dt
            
            if delta.total_seconds() < 60:
                return "just now"
            elif delta.total_seconds() < 3600:
                minutes = int(delta.total_seconds() / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif delta.date() == now.date():
                return dt.strftime("%I:%M %p")
            elif delta.date() == (now - timedelta(days=1)).date():
                return "Yesterday"
            else:
                return dt.strftime("%b %d")
        except:
            return timestamp
