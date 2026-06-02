from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid

from models import get_db, Room, AnalysisVersion
from auth.clerk import get_current_user

router = APIRouter(prefix="/correction", tags=["correction"])

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    room_type: Optional[str] = None
    area_sqft: Optional[Decimal] = None
    width_ft: Optional[Decimal] = None
    height_ft: Optional[Decimal] = None
    x: Optional[float] = None
    y: Optional[float] = None

class RoomCreate(BaseModel):
    name: str
    room_type: str
    area_sqft: Decimal
    width_ft: Decimal
    height_ft: Decimal
    x: float
    y: float

@router.put("/rooms/{room_id}")
async def update_room(
    room_id: str,
    update: RoomUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update room geometry and properties"""
    
    room = db.query(Room).filter(Room.id == uuid.UUID(room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Update room
    if update.name is not None:
        room.name = update.name
    if update.room_type is not None:
        room.room_type = update.room_type
    if update.area_sqft is not None:
        room.area_sqft = update.area_sqft
    if update.width_ft is not None:
        room.width_ft = update.width_ft
    if update.height_ft is not None:
        room.height_ft = update.height_ft
    if update.x is not None:
        room.centroid_x = Decimal(str(update.x))
    if update.y is not None:
        room.centroid_y = Decimal(str(update.y))
    
    room.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(room)
    
    return {"success": True, "room_id": str(room.id)}

@router.post("/rooms")
async def add_room(
    room: RoomCreate,
    analysis_version_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add new room manually"""
    
    # Verify analysis version exists
    analysis = db.query(AnalysisVersion).filter(
        AnalysisVersion.id == uuid.UUID(analysis_version_id)
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis version not found")
    
    # Create room
    new_room = Room(
        analysis_version_id=uuid.UUID(analysis_version_id),
        name=room.name,
        room_type=room.room_type,
        area_sqft=room.area_sqft,
        width_ft=room.width_ft,
        height_ft=room.height_ft,
        centroid_x=Decimal(str(room.x)),
        centroid_y=Decimal(str(room.y)),
        source="manual",
        confidence_score=Decimal("1.0")
    )
    
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    
    return {"success": True, "room_id": str(new_room.id)}

@router.delete("/rooms/{room_id}")
async def delete_room(
    room_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete room (soft delete)"""
    
    room = db.query(Room).filter(Room.id == uuid.UUID(room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room.is_deleted = True
    room.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}

@router.post("/analysis/{version_id}/boq-preview")
async def boq_preview(
    version_id: str,
    rooms: list[dict],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate BOQ preview for current room state"""
    
    # Verify analysis version exists
    analysis = db.query(AnalysisVersion).filter(
        AnalysisVersion.id == uuid.UUID(version_id)
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis version not found")
    
    # Calculate BOQ with current room state
    total_area = sum(r.get('area_sqft', 0) for r in rooms)
    
    # Simple BOQ calculation
    items = [
        {
            "category": "Construction",
            "description": "Basic construction work",
            "unit": "sq ft",
            "quantity": total_area,
            "rate": 150,
            "amount": total_area * 150
        },
        {
            "category": "Finishing",
            "description": "Internal finishing",
            "unit": "sq ft",
            "quantity": total_area,
            "rate": 75,
            "amount": total_area * 75
        }
    ]
    
    subtotal = sum(item["amount"] for item in items)
    gst_rate = 0.18
    gst_amount = subtotal * gst_rate
    
    return {
        "items": items,
        "subtotal": subtotal,
        "gst_amount": gst_amount,
        "gst_rate": gst_rate,
        "grand_total": subtotal + gst_amount
    }
