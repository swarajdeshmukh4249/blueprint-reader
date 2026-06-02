from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, date
import requests

class CostEngine:
    def __init__(self):
        self.external_apis = {
            'government_rates': 'https://api.example.com/gov-rates',
            'market_rates': 'https://api.example.com/market-rates'
        }
    
    async def calculate_project_cost(
        self,
        project_data: dict,
        location: dict,
        rate_card_id: Optional[str] = None
    ) -> dict:
        """Calculate total project cost based on location and rate card"""
        
        # Get applicable rate card
        rate_card = await self._get_applicable_rate_card(
            location.get('country'),
            location.get('state'),
            location.get('city'),
            rate_card_id
        )
        
        # Calculate costs for each BOQ item
        items = project_data.get('boq_items', [])
        calculated_items = []
        
        for item in items:
            calculated_item = await self._calculate_item_cost(item, rate_card)
            calculated_items.append(calculated_item)
        
        # Calculate totals
        subtotal = sum(item['amount'] for item in calculated_items)
        gst_rate = Decimal('0.18')  # 18% GST
        gst_amount = subtotal * gst_rate
        grand_total = subtotal + gst_amount
        
        return {
            'items': calculated_items,
            'subtotal': float(subtotal),
            'gst_rate': float(gst_rate),
            'gst_amount': float(gst_amount),
            'grand_total': float(grand_total),
            'rate_card_used': rate_card.get('id') if rate_card else None,
            'location': location
        }
    
    async def _get_applicable_rate_card(
        self,
        country: str,
        state: str,
        city: str,
        rate_card_id: Optional[str]
    ) -> Optional[dict]:
        """Get the most applicable rate card for the location"""
        
        # If specific rate card requested, use it
        if rate_card_id:
            # This would query the database
            return {'id': rate_card_id, 'name': 'Custom Rate Card'}
        
        # Otherwise, find the best matching rate card
        # Priority: City > State > Country > Default
        # This would query the database with location matching
        
        # For now, return a default
        return {
            'id': 'default',
            'name': 'Default Rate Card',
            'country': country,
            'state': state,
            'city': city
        }
    
    async def _calculate_item_cost(
        self,
        item: dict,
        rate_card: Optional[dict]
    ) -> dict:
        """Calculate cost for a single BOQ item"""
        
        quantity = Decimal(str(item.get('quantity', 0)))
        
        # If rate is provided, use it
        if item.get('rate'):
            rate = Decimal(str(item['rate']))
        else:
            # Look up rate from rate card
            rate = await self._lookup_rate(item, rate_card)
        
        amount = quantity * rate
        
        return {
            'category': item.get('category'),
            'description': item.get('description'),
            'unit': item.get('unit'),
            'quantity': float(quantity),
            'rate': float(rate),
            'amount': float(amount),
            'source': 'rate_card' if rate_card else 'manual'
        }
    
    async def _lookup_rate(
        self,
        item: dict,
        rate_card: Optional[dict]
    ) -> Decimal:
        """Lookup rate from rate card or external APIs"""
        
        # Try rate card first
        if rate_card:
            # This would query the rate_card_items table
            # For now, return a default rate
            return Decimal('150')
        
        # Try external APIs
        try:
            external_rate = await self._fetch_external_rate(item)
            if external_rate:
                return Decimal(str(external_rate))
        except Exception as e:
            print(f"Failed to fetch external rate: {e}")
        
        # Fallback to default
        return Decimal('150')
    
    async def _fetch_external_rate(self, item: dict) -> Optional[float]:
        """Fetch rate from external API"""
        
        # This would call external APIs to get current market rates
        # For now, return None
        return None
    
    async def get_rate_trends(
        self,
        material_name: str,
        location: dict,
        start_date: date,
        end_date: date
    ) -> List[dict]:
        """Get historical rate trends for a material"""
        
        # This would query the material_rate_history table
        # For now, return empty
        return []
    
    async def forecast_costs(
        self,
        project_data: dict,
        location: dict,
        months_ahead: int = 6
    ) -> dict:
        """Forecast future costs based on rate trends"""
        
        # Get current cost
        current_cost = await self.calculate_project_cost(project_data, location)
        
        # Get rate trends for key materials
        # Apply inflation/deflation based on trends
        
        # Simple forecast: assume 2% annual inflation
        inflation_rate = Decimal('0.02') / 12  # Monthly
        monthly_multiplier = 1 + inflation_rate
        future_multiplier = monthly_multiplier ** months_ahead
        
        forecasted_total = current_cost['grand_total'] * float(future_multiplier)
        
        return {
            'current_cost': current_cost['grand_total'],
            'forecasted_cost': forecasted_total,
            'months_ahead': months_ahead,
            'inflation_rate': 0.02,
            'confidence': 0.7
        }
