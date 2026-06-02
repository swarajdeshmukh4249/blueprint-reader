from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from models import get_db, RateCard, RateCardItem
from auth.clerk import get_current_user

router = APIRouter(prefix="/rate-cards", tags=["rate-cards"])

class RateCardCreate(BaseModel):
    organization_id: str
    name: str
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    effective_date: datetime
    expiry_date: Optional[datetime] = None
    is_default: bool = False

class RateCardItemCreate(BaseModel):
    rate_card_id: str
    item_code: Optional[str] = None
    category: Optional[str] = None
    description: str
    unit: str
    rate: float
    material_cost: Optional[float] = None
    labour_cost: Optional[float] = None
    overhead_cost: Optional[float] = None

@router.post("/")
async def create_rate_card(
    rate_card: RateCardCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new rate card"""
    
    new_rate_card = RateCard(
        organization_id=uuid.UUID(rate_card.organization_id),
        name=rate_card.name,
        country=rate_card.country,
        state=rate_card.state,
        city=rate_card.city,
        effective_date=rate_card.effective_date,
        expiry_date=rate_card.expiry_date,
        is_default=rate_card.is_default
    )
    
    db.add(new_rate_card)
    db.commit()
    db.refresh(new_rate_card)
    
    return {"id": str(new_rate_card.id), "name": new_rate_card.name}

@router.get("/organization/{organization_id}")
async def list_rate_cards(
    organization_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all rate cards for an organization"""
    
    rate_cards = db.query(RateCard).filter(
        RateCard.organization_id == uuid.UUID(organization_id)
    ).all()
    
    return [
        {
            "id": str(rc.id),
            "name": rc.name,
            "country": rc.country,
            "state": rc.state,
            "city": rc.city,
            "effective_date": rc.effective_date.isoformat(),
            "expiry_date": rc.expiry_date.isoformat() if rc.expiry_date else None,
            "is_default": rc.is_default
        }
        for rc in rate_cards
    ]

@router.post("/items")
async def add_rate_card_item(
    item: RateCardItemCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an item to a rate card"""
    
    new_item = RateCardItem(
        rate_card_id=uuid.UUID(item.rate_card_id),
        item_code=item.item_code,
        category=item.category,
        description=item.description,
        unit=item.unit,
        rate=item.rate,
        material_cost=item.material_cost,
        labour_cost=item.labour_cost,
        overhead_cost=item.overhead_cost
    )
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return {"id": str(new_item.id)}

@router.get("/{rate_card_id}/items")
async def list_rate_card_items(
    rate_card_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all items in a rate card"""
    
    items = db.query(RateCardItem).filter(
        RateCardItem.rate_card_id == uuid.UUID(rate_card_id)
    ).all()
    
    return [
        {
            "id": str(item.id),
            "item_code": item.item_code,
            "category": item.category,
            "description": item.description,
            "unit": item.unit,
            "rate": float(item.rate),
            "material_cost": float(item.material_cost) if item.material_cost else None,
            "labour_cost": float(item.labour_cost) if item.labour_cost else None,
            "overhead_cost": float(item.overhead_cost) if item.overhead_cost else None
        }
        for item in items
    ]
