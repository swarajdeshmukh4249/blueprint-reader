"""
Correction Service
Handles manual room corrections with undo support
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from config import ALLOWED_ROOM_TYPES, ALLOWED_WALL_TYPES, MAX_FLOORS
from utils.errors import (
    RoomNameValidationError,
    RoomTypeError,
    DimensionValidationError,
    FloorValidationError
)


class CorrectionService:
    """Manages manual room corrections with undo support"""
    
    def __init__(self):
        """Initialize the correction service"""
        self.corrections_log = []
    
    def edit_room(
        self,
        room: Dict[str, Any],
        changes: Dict[str, Any],
        edited_by: str
    ) -> Dict[str, Any]:
        """
        Edit a room with validation
        
        Args:
            room: Current room data
            changes: Dictionary of fields to change
            edited_by: ID of user making the edit
            
        Returns:
            Updated room with BOQ impact preview
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate changes
        self._validate_room_changes(changes, room)
        
        # Log changes
        for field, new_value in changes.items():
            if field in room:
                old_value = room[field]
                if old_value != new_value:
                    self.corrections_log.append({
                        "room_id": room.get("id"),
                        "field_changed": field,
                        "old_value": old_value,
                        "new_value": new_value,
                        "edited_by": edited_by,
                        "edited_at": datetime.utcnow().isoformat()
                    })
        
        # Apply changes
        updated_room = room.copy()
        updated_room.update(changes)
        
        # Recalculate area if dimensions changed
        if "width_m" in changes or "height_m" in changes:
            updated_room["area_m2"] = updated_room["width_m"] * updated_room["height_m"]
        
        # Mark as verified
        updated_room["is_verified"] = True
        updated_room["source"] = "user_corrected"
        
        # Calculate BOQ impact preview
        boq_impact = self._calculate_boq_impact(room, updated_room)
        
        return {
            "room": updated_room,
            "boq_impact": boq_impact
        }
    
    def add_room(
        self,
        rooms: List[Dict[str, Any]],
        new_room: Dict[str, Any],
        added_by: str
    ) -> Dict[str, Any]:
        """
        Add a new room
        
        Args:
            rooms: Current list of rooms
            new_room: New room data
            added_by: ID of user adding the room
            
        Returns:
            Updated rooms list with new room
        """
        # Validate required fields
        if not new_room.get("name"):
            raise RoomNameValidationError("Room name is required")
        
        if not new_room.get("room_type"):
            raise RoomTypeError("Room type is required")
        
        if new_room["room_type"] not in ALLOWED_ROOM_TYPES:
            raise RoomTypeError(new_room["room_type"])
        
        # Set defaults
        room_id = str(uuid.uuid4())
        new_room["id"] = room_id
        new_room["source"] = "user_added"
        new_room["is_verified"] = True
        new_room["created_at"] = datetime.utcnow().isoformat()
        new_room["created_by"] = added_by
        
        # If dimensions not provided, mark for calibration
        if not new_room.get("width_m") or not new_room.get("height_m"):
            new_room["needs_calibration"] = True
            new_room["width_m"] = 0
            new_room["height_m"] = 0
            new_room["area_m2"] = 0
        else:
            new_room["needs_calibration"] = False
            new_room["area_m2"] = new_room["width_m"] * new_room["height_m"]
        
        # Set defaults for optional fields
        new_room.setdefault("wall_type", "partition")
        new_room.setdefault("floor", 1)
        new_room.setdefault("x", 0)
        new_room.setdefault("y", 0)
        new_room.setdefault("width_px", 0)
        new_room.setdefault("height_px", 0)
        new_room.setdefault("confidence", 1.0)
        
        # Add to rooms list
        updated_rooms = rooms + [new_room]
        
        # Calculate BOQ impact
        boq_impact = self._calculate_add_room_impact(new_room)
        
        return {
            "rooms": updated_rooms,
            "new_room": new_room,
            "boq_impact": boq_impact
        }
    
    def delete_room(
        self,
        rooms: List[Dict[str, Any]],
        room_id: str,
        deleted_by: str
    ) -> Dict[str, Any]:
        """
        Delete a room (soft delete)
        
        Args:
            rooms: Current list of rooms
            room_id: ID of room to delete
            deleted_by: ID of user deleting the room
            
        Returns:
            Updated rooms list and BOQ impact
        """
        # Find room
        room_to_delete = None
        room_index = None
        for i, room in enumerate(rooms):
            if room.get("id") == room_id:
                room_to_delete = room
                room_index = i
                break
        
        if not room_to_delete:
            raise ValueError(f"Room with ID {room_id} not found")
        
        # Check if it's the only room on its floor
        floor = room_to_delete.get("floor", 1)
        rooms_on_floor = [r for r in rooms if r.get("floor") == floor and not r.get("is_deleted")]
        
        if len(rooms_on_floor) == 1:
            return {
                "warning": "This is the only room on this floor. Deleting it will make the floor empty.",
                "rooms": rooms,
                "boq_impact": None,
                "confirm_required": True
            }
        
        # Soft delete
        updated_rooms = []
        for room in rooms:
            if room.get("id") == room_id:
                deleted_room = room.copy()
                deleted_room["is_deleted"] = True
                deleted_room["deleted_by"] = deleted_by
                deleted_room["deleted_at"] = datetime.utcnow().isoformat()
                updated_rooms.append(deleted_room)
            else:
                updated_rooms.append(room)
        
        # Calculate BOQ impact
        boq_impact = self._calculate_delete_room_impact(room_to_delete)
        
        return {
            "rooms": updated_rooms,
            "deleted_room": room_to_delete,
            "boq_impact": boq_impact,
            "confirm_required": False
        }
    
    def undo_correction(
        self,
        rooms: List[Dict[str, Any]],
        correction_id: str
    ) -> Dict[str, Any]:
        """
        Undo a specific correction
        
        Args:
            rooms: Current list of rooms
            correction_id: ID of correction to undo
            
        Returns:
            Updated rooms list
        """
        # Find correction
        correction = None
        for c in self.corrections_log:
            if str(uuid.UUID(c.get("room_id", ""))) == correction_id:
                correction = c
                break
        
        if not correction:
            raise ValueError(f"Correction with ID {correction_id} not found")
        
        # Find room and revert change
        updated_rooms = []
        for room in rooms:
            if room.get("id") == correction["room_id"]:
                reverted_room = room.copy()
                reverted_room[correction["field_changed"]] = correction["old_value"]
                updated_rooms.append(reverted_room)
            else:
                updated_rooms.append(room)
        
        # Remove correction from log
        self.corrections_log = [
            c for c in self.corrections_log
            if c != correction
        ]
        
        return {
            "rooms": updated_rooms,
            "undone_correction": correction
        }
    
    def get_corrections_history(self, room_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get corrections history
        
        Args:
            room_id: Optional room ID to filter by
            
        Returns:
            List of corrections
        """
        if room_id:
            return [c for c in self.corrections_log if c.get("room_id") == room_id]
        return self.corrections_log
    
    def _validate_room_changes(self, changes: Dict[str, Any], room: Dict[str, Any]):
        """Validate room changes"""
        
        # Validate name
        if "name" in changes:
            name = changes["name"]
            if not name or name.strip() == "":
                raise RoomNameValidationError("Room name cannot be empty")
            if len(name) > 100:
                raise RoomNameValidationError("Room name too long (max 100 characters)")
        
        # Validate room type
        if "room_type" in changes:
            room_type = changes["room_type"]
            if room_type not in ALLOWED_ROOM_TYPES:
                raise RoomTypeError(room_type)
        
        # Validate dimensions
        for field in ["width_m", "height_m"]:
            if field in changes:
                value = changes[field]
                if value is not None:
                    if value <= 0:
                        raise DimensionValidationError(
                            field,
                            f"{field.replace('_', ' ').title()} must be greater than 0"
                        )
                    if value > 500:
                        # Warning, not error
                        pass  # Could add a warning field to response
        
        # Validate floor
        if "floor" in changes:
            floor = changes["floor"]
            if floor < 1 or floor > MAX_FLOORS:
                raise FloorValidationError(floor)
    
    def _calculate_boq_impact(self, old_room: Dict[str, Any], new_room: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate BOQ impact of room changes"""
        impact = {
            "changed_fields": [],
            "area_delta_m2": 0.0,
            "cost_delta": 0.0
        }
        
        # Check which fields changed
        for field in ["width_m", "height_m", "room_type", "wall_type"]:
            if field in new_room and new_room[field] != old_room.get(field):
                impact["changed_fields"].append(field)
        
        # Calculate area delta
        old_area = old_room.get("area_m2", 0)
        new_area = new_room.get("area_m2", 0)
        impact["area_delta_m2"] = new_area - old_area
        
        # Estimate cost delta (simplified)
        # In production, this would use the BOQ calculator
        cost_per_sqft = 100  # Simplified rate
        impact["cost_delta"] = impact["area_delta_m2"] * cost_per_sqft * 10.764  # Convert to sq ft
        
        return impact
    
    def _calculate_add_room_impact(self, new_room: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate BOQ impact of adding a room"""
        area = new_room.get("area_m2", 0)
        cost_per_sqft = 100  # Simplified rate
        
        return {
            "action": "added",
            "area_m2": area,
            "cost_estimate": area * cost_per_sqft * 10.764
        }
    
    def _calculate_delete_room_impact(self, deleted_room: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate BOQ impact of deleting a room"""
        area = deleted_room.get("area_m2", 0)
        cost_per_sqft = 100  # Simplified rate
        
        return {
            "action": "deleted",
            "area_m2": area,
            "cost_estimate": area * cost_per_sqft * 10.764
        }
