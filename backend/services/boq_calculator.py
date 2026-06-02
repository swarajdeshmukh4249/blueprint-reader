"""
BOQ Calculator Service
Generates Bill of Quantities from room data
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from config import SUPPORTED_UNITS


class BOQCalculator:
    """Calculates BOQ from room data"""
    
    def __init__(self, rate_card: Optional[Dict[str, Any]] = None):
        """
        Initialize BOQ calculator
        
        Args:
            rate_card: Optional rate card with material and labor rates
        """
        self.rate_card = rate_card or self._default_rate_card()
    
    def calculate_boq(self, rooms: List[Dict[str, Any]], scale_factor: float = 1.0) -> Dict[str, Any]:
        """
        Calculate BOQ from room data
        
        Args:
            rooms: List of room dictionaries with dimensions
            scale_factor: Scale factor to convert pixels to meters
            
        Returns:
            BOQ with line items, cost breakdown, and totals
        """
        line_items = []
        total_area_m2 = 0.0
        total_cost = 0.0
        
        # Calculate for each room
        for room in rooms:
            room_items = self._calculate_room_items(room, scale_factor)
            line_items.extend(room_items)
            
            # Add room area to total
            room_area = room.get("area_m2", 0.0)
            total_area_m2 += room_area
        
        # Calculate totals
        for item in line_items:
            total_cost += item.get("amount", 0.0)
        
        # Group by category for breakdown
        cost_breakdown = self._calculate_cost_breakdown(line_items)
        
        return {
            "line_items": line_items,
            "total_area_m2": total_area_m2,
            "total_cost": total_cost,
            "cost_breakdown": cost_breakdown,
            "currency": "INR"
        }
    
    def _calculate_room_items(self, room: Dict[str, Any], scale_factor: float) -> List[Dict[str, Any]]:
        """
        Calculate BOQ items for a single room
        
        Args:
            room: Room dictionary with dimensions
            scale_factor: Scale factor to convert pixels to meters
            
        Returns:
            List of BOQ line items for this room
        """
        items = []
        room_type = room.get("room_type", "unknown")
        width_m = room.get("width_m", 0.0)
        height_m = room.get("height_m", 0.0)
        area_m2 = width_m * height_m
        perimeter_m = 2 * (width_m + height_m)
        
        # Get rates for this room type
        rates = self.rate_card.get(room_type, self.rate_card.get("default", {}))
        
        # 1. Flooring
        flooring_rate = rates.get("flooring_per_sqft", 50)
        flooring_cost = area_m2 * flooring_rate
        items.append({
            "item_code": "FLR-001",
            "description": f"{room_type.title()} Flooring",
            "unit": "sq ft",
            "quantity": area_m2 * 10.764,  # Convert m2 to sq ft
            "rate": flooring_rate,
            "amount": flooring_cost,
            "category": "Flooring",
            "room_id": room.get("id"),
            "room_name": room.get("name")
        })
        
        # 2. Wall plastering
        wall_height = 3.0  # Standard wall height in meters
        wall_area = perimeter_m * wall_height
        plastering_rate = rates.get("plastering_per_sqft", 25)
        plastering_cost = wall_area * plastering_rate
        items.append({
            "item_code": "WAL-001",
            "description": f"{room_type.title()} Wall Plastering",
            "unit": "sq ft",
            "quantity": wall_area * 10.764,
            "rate": plastering_rate,
            "amount": plastering_cost,
            "category": "Walls",
            "room_id": room.get("id"),
            "room_name": room.get("name")
        })
        
        # 3. Painting
        painting_rate = rates.get("painting_per_sqft", 20)
        painting_cost = wall_area * painting_rate
        items.append({
            "item_code": "PNT-001",
            "description": f"{room_type.title()} Painting",
            "unit": "sq ft",
            "quantity": wall_area * 10.764,
            "rate": painting_rate,
            "amount": painting_cost,
            "category": "Finishing",
            "room_id": room.get("id"),
            "room_name": room.get("name")
        })
        
        # 4. Electrical (fixed per room)
        electrical_rate = rates.get("electrical_per_room", 5000)
        items.append({
            "item_code": "ELE-001",
            "description": f"{room_type.title()} Electrical Works",
            "unit": "ls",
            "quantity": 1,
            "rate": electrical_rate,
            "amount": electrical_rate,
            "category": "Services",
            "room_id": room.get("id"),
            "room_name": room.get("name")
        })
        
        # 5. Plumbing (for bathrooms and kitchens)
        if room_type in ["bathroom", "kitchen", "utility"]:
            plumbing_rate = rates.get("plumbing_per_room", 8000)
            items.append({
                "item_code": "PLB-001",
                "description": f"{room_type.title()} Plumbing Works",
                "unit": "ls",
                "quantity": 1,
                "rate": plumbing_rate,
                "amount": plumbing_rate,
                "category": "Services",
                "room_id": room.get("id"),
                "room_name": room.get("name")
            })
        
        return items
    
    def _calculate_cost_breakdown(self, line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate cost breakdown by category
        
        Args:
            line_items: List of BOQ line items
            
        Returns:
            Cost breakdown by category
        """
        breakdown = {}
        
        for item in line_items:
            category = item.get("category", "Other")
            amount = item.get("amount", 0.0)
            
            if category not in breakdown:
                breakdown[category] = 0.0
            
            breakdown[category] += amount
        
        # Calculate percentages
        total = sum(breakdown.values())
        breakdown_with_percentage = {}
        
        for category, amount in breakdown.items():
            percentage = (amount / total * 100) if total > 0 else 0.0
            breakdown_with_percentage[category] = {
                "amount": amount,
                "percentage": round(percentage, 2)
            }
        
        return breakdown_with_percentage
    
    def recalculate_boq(
        self,
        rooms: List[Dict[str, Any]],
        changed_room_ids: List[str],
        scale_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        Recalculate BOQ for only changed rooms
        
        Args:
            rooms: List of all rooms
            changed_room_ids: List of room IDs that changed
            scale_factor: Scale factor to convert pixels to meters
            
        Returns:
            BOQ with diff showing what changed
        """
        # Calculate full BOQ
        full_boq = self.calculate_boq(rooms, scale_factor)
        
        # Calculate BOQ for changed rooms only
        changed_rooms = [r for r in rooms if r.get("id") in changed_room_ids]
        changed_boq = self.calculate_boq(changed_rooms, scale_factor)
        
        # Calculate diff
        diff = {
            "changed_rooms": changed_room_ids,
            "old_total": full_boq["total_cost"] - changed_boq["total_cost"],
            "new_total": full_boq["total_cost"],
            "delta": changed_boq["total_cost"]
        }
        
        return {
            **full_boq,
            "diff": diff
        }
    
    def _default_rate_card(self) -> Dict[str, Any]:
        """
        Default rate card for BOQ calculation
        
        Returns:
            Default rate card with standard rates
        """
        return {
            "default": {
                "flooring_per_sqft": 50,
                "plastering_per_sqft": 25,
                "painting_per_sqft": 20,
                "electrical_per_room": 5000,
                "plumbing_per_room": 8000
            },
            "bedroom": {
                "flooring_per_sqft": 60,
                "plastering_per_sqft": 25,
                "painting_per_sqft": 20,
                "electrical_per_room": 5000
            },
            "bathroom": {
                "flooring_per_sqft": 80,
                "plastering_per_sqft": 30,
                "painting_per_sqft": 25,
                "electrical_per_room": 3000,
                "plumbing_per_room": 12000
            },
            "kitchen": {
                "flooring_per_sqft": 70,
                "plastering_per_sqft": 30,
                "painting_per_sqft": 25,
                "electrical_per_room": 6000,
                "plumbing_per_room": 10000
            },
            "living_room": {
                "flooring_per_sqft": 65,
                "plastering_per_sqft": 25,
                "painting_per_sqft": 20,
                "electrical_per_room": 6000
            },
            "corridor": {
                "flooring_per_sqft": 40,
                "plastering_per_sqft": 20,
                "painting_per_sqft": 15,
                "electrical_per_room": 2000
            }
        }
