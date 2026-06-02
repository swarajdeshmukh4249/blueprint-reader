from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
import uuid

from models import get_db
from auth.clerk import get_current_user
from services.cost_engine import CostEngine

router = APIRouter(prefix="/cost-engine", tags=["cost-engine"])
cost_engine = CostEngine()

class CostCalculationRequest(BaseModel):
    project_data: dict
    location: dict
    rate_card_id: Optional[str] = None

class CostForecastRequest(BaseModel):
    project_data: dict
    location: dict
    months_ahead: int = 6

@router.post("/calculate")
async def calculate_cost(
    request: CostCalculationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate project cost based on location and rate card"""
    
    result = await cost_engine.calculate_project_cost(
        request.project_data,
        request.location,
        request.rate_card_id
    )
    
    return result

@router.post("/forecast")
async def forecast_cost(
    request: CostForecastRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Forecast future costs based on rate trends"""
    
    result = await cost_engine.forecast_costs(
        request.project_data,
        request.location,
        request.months_ahead
    )
    
    return result

@router.get("/rate-trends/{material_name}")
async def get_rate_trends(
    material_name: str,
    country: str,
    state: Optional[str] = None,
    city: Optional[str] = None,
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get historical rate trends for a material"""
    
    location = {
        'country': country,
        'state': state,
        'city': city
    }
    
    trends = await cost_engine.get_rate_trends(
        material_name,
        location,
        start_date,
        end_date
    )
    
    return {
        'material_name': material_name,
        'location': location,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'trends': trends
    }
