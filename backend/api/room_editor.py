from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from models import get_db, Room, AnalysisVersion, BOQItem
from auth.clerk import get_current_user_db, User
from boq_engine import generate_boq

router = APIRouter(prefix="/room-editor", tags=["room-editor"])

class RoomUpdate(BaseModel):
    id: str
    name: Optional[str] = None
    room_type: Optional[str] = None
    width_ft: Optional[float] = None
    height_ft: Optional[float] = None
    width_m: Optional[float] = None
    height_m: Optional[float] = None
    area_sqft: Optional[float] = None
    area_sqm: Optional[float] = None
    polygon_coordinates: Optional[List[List[float]]] = None

class RoomCreate(BaseModel):
    analysis_version_id: str
    name: str
    room_type: Optional[str] = None
    width_ft: Optional[float] = None
    height_ft: Optional[float] = None
    width_m: Optional[float] = None
    height_m: Optional[float] = None
    area_sqft: Optional[float] = None
    area_sqm: Optional[float] = None
    polygon_coordinates: Optional[List[List[float]]] = None
    floor_number: Optional[int] = 1

class RoomSplitRequest(BaseModel):
    room_id: str
    split_direction: str  # "horizontal" or "vertical"
    split_ratio: float = 0.5  # 0.5 for equal split

class RoomMergeRequest(BaseModel):
    room_ids: List[str]
    new_name: Optional[str] = None
    new_room_type: Optional[str] = None

class WindowDoorCreate(BaseModel):
    room_id: str
    opening_type: str  # "door" or "window"
    width_ft: Optional[float] = None
    height_ft: Optional[float] = None
    width_m: Optional[float] = None
    height_m: Optional[float] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None

@router.put("/rooms/{room_id}")
async def update_room(
    room_id: str,
    room_update: RoomUpdate,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Update a single room and trigger BOQ recalculation"""
    
    room = db.query(Room).filter(Room.id == uuid.UUID(room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Update room fields
    if room_update.name is not None:
        room.name = room_update.name
    if room_update.room_type is not None:
        room.room_type = room_update.room_type
    if room_update.width_ft is not None:
        room.width_ft = room_update.width_ft
    if room_update.height_ft is not None:
        room.height_ft = room_update.height_ft
    if room_update.width_m is not None:
        room.width_m = room_update.width_m
    if room_update.height_m is not None:
        room.height_m = room_update.height_m
    if room_update.area_sqft is not None:
        room.area_sqft = room_update.area_sqft
    if room_update.area_sqm is not None:
        room.area_sqm = room_update.area_sqm
    if room_update.polygon_coordinates is not None:
        room.polygon_coordinates = room_update.polygon_coordinates
    
    room.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(room)
    
    # Trigger BOQ recalculation
    analysis_version_id = room.analysis_version_id
    updated_boq = _recalculate_boq(analysis_version_id, db)
    
    return {
        "room": {
            "id": str(room.id),
            "name": room.name,
            "room_type": room.room_type,
            "width_ft": float(room.width_ft) if room.width_ft else None,
            "height_ft": float(room.height_ft) if room.height_ft else None,
            "width_m": float(room.width_m) if room.width_m else None,
            "height_m": float(room.height_m) if room.height_m else None,
            "area_sqft": float(room.area_sqft) if room.area_sqft else None,
            "area_sqm": float(room.area_sqm) if room.area_sqm else None,
            "polygon_coordinates": room.polygon_coordinates,
        },
        "boq": updated_boq
    }

@router.post("/rooms")
async def create_room(
    room_create: RoomCreate,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Create a new room and trigger BOQ recalculation"""
    
    # Verify analysis version exists
    analysis = db.query(AnalysisVersion).filter(
        AnalysisVersion.id == uuid.UUID(room_create.analysis_version_id)
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis version not found")
    
    # Create new room
    new_room = Room(
        analysis_version_id=uuid.UUID(room_create.analysis_version_id),
        name=room_create.name,
        room_type=room_create.room_type,
        width_ft=room_create.width_ft,
        height_ft=room_create.height_ft,
        width_m=room_create.width_m,
        height_m=room_create.height_m,
        area_sqft=room_create.area_sqft,
        area_sqm=room_create.area_sqm,
        polygon_coordinates=room_create.polygon_coordinates,
        floor_number=room_create.floor_number or 1,
        confidence_score=1.0,  # Manual edits have high confidence
        source="manual_edit"
    )
    
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    
    # Trigger BOQ recalculation
    updated_boq = _recalculate_boq(uuid.UUID(room_create.analysis_version_id), db)
    
    return {
        "room": {
            "id": str(new_room.id),
            "name": new_room.name,
            "room_type": new_room.room_type,
            "width_ft": float(new_room.width_ft) if new_room.width_ft else None,
            "height_ft": float(new_room.height_ft) if new_room.height_ft else None,
            "width_m": float(new_room.width_m) if new_room.width_m else None,
            "height_m": float(new_room.height_m) if new_room.height_m else None,
            "area_sqft": float(new_room.area_sqft) if new_room.area_sqft else None,
            "area_sqm": float(new_room.area_sqm) if new_room.area_sqm else None,
            "polygon_coordinates": new_room.polygon_coordinates,
        },
        "boq": updated_boq
    }

@router.delete("/rooms/{room_id}")
async def delete_room(
    room_id: str,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Delete a room (soft delete) and trigger BOQ recalculation"""
    
    room = db.query(Room).filter(Room.id == uuid.UUID(room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    analysis_version_id = room.analysis_version_id
    
    # Soft delete
    room.is_deleted = True
    room.updated_at = datetime.utcnow()
    db.commit()
    
    # Trigger BOQ recalculation
    updated_boq = _recalculate_boq(analysis_version_id, db)
    
    return {
        "success": True,
        "boq": updated_boq
    }

@router.post("/rooms/split")
async def split_room(
    split_request: RoomSplitRequest,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Split a room into two rooms and trigger BOQ recalculation"""
    
    room = db.query(Room).filter(Room.id == uuid.UUID(split_request.room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Calculate new dimensions based on split direction
    if split_request.split_direction == "horizontal":
        # Split horizontally (top/bottom)
        new_height_ft = float(room.height_ft) * split_request.split_ratio if room.height_ft else None
        new_height_m = float(room.height_m) * split_request.split_ratio if room.height_m else None
        new_area_sqft = float(room.area_sqft) * split_request.split_ratio if room.area_sqft else None
        new_area_sqm = float(room.area_sqm) * split_request.split_ratio if room.area_sqm else None
    else:
        # Split vertically (left/right)
        new_width_ft = float(room.width_ft) * split_request.split_ratio if room.width_ft else None
        new_width_m = float(room.width_m) * split_request.split_ratio if room.width_m else None
        new_area_sqft = float(room.area_sqft) * split_request.split_ratio if room.area_sqft else None
        new_area_sqm = float(room.area_sqm) * split_request.split_ratio if room.area_sqm else None
    
    # Update original room
    if split_request.split_direction == "horizontal":
        if room.height_ft:
            room.height_ft = new_height_ft
        if room.height_m:
            room.height_m = new_height_m
    else:
        if room.width_ft:
            room.width_ft = new_width_ft
        if room.width_m:
            room.width_m = new_width_m
    
    if room.area_sqft:
        room.area_sqft = new_area_sqft
    if room.area_sqm:
        room.area_sqm = new_area_sqm
    
    room.updated_at = datetime.utcnow()
    
    # Create second room
    second_room = Room(
        analysis_version_id=room.analysis_version_id,
        name=f"{room.name} (Split)",
        room_type=room.room_type,
        width_ft=room.width_ft,
        height_ft=room.height_ft,
        width_m=room.width_m,
        height_m=room.height_m,
        area_sqft=float(room.area_sqft) * (1 - split_request.split_ratio) if room.area_sqft else None,
        area_sqm=float(room.area_sqm) * (1 - split_request.split_ratio) if room.area_sqm else None,
        polygon_coordinates=room.polygon_coordinates,
        floor_number=room.floor_number,
        confidence_score=0.9,
        source="manual_split"
    )
    
    db.add(second_room)
    db.commit()
    db.refresh(room)
    db.refresh(second_room)
    
    # Trigger BOQ recalculation
    updated_boq = _recalculate_boq(room.analysis_version_id, db)
    
    return {
        "original_room": {
            "id": str(room.id),
            "name": room.name,
            "area_sqft": float(room.area_sqft) if room.area_sqft else None,
        },
        "new_room": {
            "id": str(second_room.id),
            "name": second_room.name,
            "area_sqft": float(second_room.area_sqft) if second_room.area_sqft else None,
        },
        "boq": updated_boq
    }

@router.post("/rooms/merge")
async def merge_rooms(
    merge_request: RoomMergeRequest,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Merge multiple rooms into one and trigger BOQ recalculation"""
    
    rooms = db.query(Room).filter(
        Room.id.in_([uuid.UUID(rid) for rid in merge_request.room_ids])
    ).all()
    
    if len(rooms) < 2:
        raise HTTPException(status_code=400, detail="At least 2 rooms required for merge")
    
    analysis_version_id = rooms[0].analysis_version_id
    
    # Calculate combined area
    total_area_sqft = sum(float(r.area_sqft) for r in rooms if r.area_sqft)
    total_area_sqm = sum(float(r.area_sqm) for r in rooms if r.area_sqm)
    
    # Create merged room
    merged_room = Room(
        analysis_version_id=analysis_version_id,
        name=merge_request.new_name or "Merged Room",
        room_type=merge_request.new_room_type or rooms[0].room_type,
        area_sqft=total_area_sqft,
        area_sqm=total_area_sqm,
        floor_number=rooms[0].floor_number,
        confidence_score=0.85,
        source="manual_merge"
    )
    
    db.add(merged_room)
    
    # Soft delete original rooms
    for room in rooms:
        room.is_deleted = True
        room.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(merged_room)
    
    # Trigger BOQ recalculation
    updated_boq = _recalculate_boq(analysis_version_id, db)
    
    return {
        "merged_room": {
            "id": str(merged_room.id),
            "name": merged_room.name,
            "area_sqft": float(merged_room.area_sqft) if merged_room.area_sqft else None,
        },
        "boq": updated_boq
    }

@router.post("/rooms/{room_id}/openings")
async def add_opening(
    room_id: str,
    opening: WindowDoorCreate,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Add a window or door to a room and trigger BOQ recalculation"""
    
    room = db.query(Room).filter(Room.id == uuid.UUID(room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Import Openings model
    from models import Openings
    
    new_opening = Openings(
        room_id=uuid.UUID(room_id),
        analysis_version_id=room.analysis_version_id,
        opening_type=opening.opening_type,
        width_ft=opening.width_ft,
        height_ft=opening.height_ft,
        width_m=opening.width_m,
        height_m=opening.height_m,
        position_x=opening.position_x,
        position_y=opening.position_y,
        confidence_score=1.0
    )
    
    db.add(new_opening)
    db.commit()
    db.refresh(new_opening)
    
    # Trigger BOQ recalculation
    updated_boq = _recalculate_boq(room.analysis_version_id, db)
    
    return {
        "opening": {
            "id": str(new_opening.id),
            "opening_type": new_opening.opening_type,
            "width_ft": float(new_opening.width_ft) if new_opening.width_ft else None,
            "height_ft": float(new_opening.height_ft) if new_opening.height_ft else None,
        },
        "boq": updated_boq
    }

def _recalculate_boq(analysis_version_id: uuid.UUID, db: Session) -> dict:
    """Recalculate BOQ for an analysis version"""
    # Get all rooms for this analysis
    rooms = db.query(Room).filter(
        Room.analysis_version_id == analysis_version_id,
        Room.is_deleted == False
    ).all()
    
    # Convert to format expected by BOQ engine
    room_data = []
    for room in rooms:
        room_data.append({
            "room": room.name,
            "area": float(room.area_sqft) if room.area_sqft else 0,
            "unit": "sq ft",
            "room_type": room.room_type or "unknown"
        })
    
    # Generate BOQ
    analysis_result = {"room_data": room_data}
    boq_result = generate_boq(analysis_result)
    
    # Update BOQ items in database
    # Delete existing BOQ items
    db.query(BOQItem).filter(
        BOQItem.analysis_version_id == analysis_version_id
    ).delete()
    
    # Add new BOQ items
    if boq_result.get("boq_items"):
        for item in boq_result["boq_items"]:
            boq_item = BOQItem(
                analysis_version_id=analysis_version_id,
                category=item.get("category", "Unknown"),
                item_code=item.get("item_code"),
                description=item.get("description", ""),
                unit=item.get("unit", "sq ft"),
                quantity=item.get("quantity"),
                rate=item.get("rate"),
                amount=item.get("amount"),
                source="manual_edit"
            )
            db.add(boq_item)
    
    db.commit()
    
    return boq_result
