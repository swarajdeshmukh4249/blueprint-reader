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
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent activities
        
        Args:
            limit: Maximum number of activities to return
            project_id: Optional project ID to filter by
            organization_id: Optional organization ID to filter by
            
        Returns:
            List of activity events
        """
        # In production, this would query a database table
        # For now, we'll generate activities from existing data
        
        activities = []
        
        # Generate activities from recent files
        files = self.db.query(BlueprintFile).order_by(
            BlueprintFile.created_at.desc()
        ).limit(limit)
        
        if organization_id:
            files = files.join(Project).filter(
                Project.organization_id == uuid.UUID(organization_id)
            )
        
        for file in files:
            activities.append({
                "id": str(uuid.uuid4()),
                "event_type": "file_uploaded",
                "description": f"New blueprint uploaded — {file.name}",
                "project_id": str(file.project_id),
                "user_id": None,
                "metadata": {"file_id": str(file.id)},
                "created_at": file.created_at.isoformat() if file.created_at else datetime.utcnow().isoformat()
            })
        
        # Generate activities from analyses
        analyses = self.db.query(AnalysisVersion).order_by(
            AnalysisVersion.created_at.desc()
        ).limit(limit)
        
        if organization_id:
            analyses = analyses.join(Project).filter(
                Project.organization_id == uuid.UUID(organization_id)
            )
        
        for analysis in analyses:
            if analysis.status == "completed":
                activities.append({
                    "id": str(uuid.uuid4()),
                    "event_type": "boq_generated",
                    "description": f"BOQ generated for project",
                    "project_id": str(analysis.project_id),
                    "user_id": None,
                    "metadata": {"analysis_id": str(analysis.id)},
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else datetime.utcnow().isoformat()
                })
            elif analysis.status == "failed":
                activities.append({
                    "id": str(uuid.uuid4()),
                    "event_type": "analysis_failed",
                    "description": f"Analysis failed for project",
                    "project_id": str(analysis.project_id),
                    "user_id": None,
                    "metadata": {"analysis_id": str(analysis.id)},
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else datetime.utcnow().isoformat()
                })
        
        # Sort by created_at and limit
        activities.sort(key=lambda x: x["created_at"], reverse=True)
        activities = activities[:limit]
        
        # Format timestamps
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
