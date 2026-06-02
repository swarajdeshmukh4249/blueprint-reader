"""
Room Matcher Service
Floor comparison matching algorithm with weighted scores
"""
from typing import Dict, Any, List, Tuple, Optional
from config import ROOM_MATCH_THRESHOLD
from utils.errors import ComparisonError


class RoomMatcher:
    """Matches rooms between two floors using weighted scoring"""
    
    def __init__(self):
        """Initialize the room matcher"""
        self.name_weight = 0.45
        self.type_weight = 0.25
        self.area_weight = 0.20
        self.position_weight = 0.10
    
    def compare_floors(
        self,
        floor_a: Dict[str, Any],
        floor_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two floors and match rooms
        
        Args:
            floor_a: First floor data with rooms
            floor_b: Second floor data with rooms
            
        Returns:
            Comparison result with room diffs and summary
        """
        rooms_a = floor_a.get("rooms", [])
        rooms_b = floor_b.get("rooms", [])
        
        # Check for empty floors
        if not rooms_a and not rooms_b:
            return self._empty_comparison_result(floor_a, floor_b)
        
        if not rooms_a:
            return self._all_added_result(floor_a, floor_b, rooms_b)
        
        if not rooms_b:
            return self._all_removed_result(floor_a, floor_b, rooms_a)
        
        # Match rooms
        room_diffs = []
        matched_pairs = []
        unmatched_a = set(range(len(rooms_a)))
        unmatched_b = set(range(len(rooms_b)))
        
        # Find best matches for each room in floor_a
        for i, room_a in enumerate(rooms_a):
            best_match = None
            best_score = 0.0
            
            for j, room_b in enumerate(rooms_b):
                if j in unmatched_b:
                    score = self._calculate_match_score(room_a, room_b)
                    
                    if score > best_score:
                        best_score = score
                        best_match = (j, score)
            
            if best_match and best_match[1] >= ROOM_MATCH_THRESHOLD:
                j, score = best_match
                room_b = rooms_b[j]
                
                # Determine status
                if score >= 0.95:
                    status = "match"
                elif score >= ROOM_MATCH_THRESHOLD:
                    status = "changed"
                else:
                    status = "changed"
                
                # Calculate area delta
                area_delta = room_b.get("area_m2", 0) - room_a.get("area_m2", 0)
                
                room_diffs.append({
                    "room_name": room_a.get("name", "Unknown"),
                    "room_type": room_a.get("room_type", "unknown"),
                    "status": status,
                    "area_a": room_a.get("area_m2", 0),
                    "area_b": room_b.get("area_m2", 0),
                    "area_delta_m2": area_delta,
                    "match_score": score,
                    "room_a_id": room_a.get("id"),
                    "room_b_id": room_b.get("id")
                })
                
                matched_pairs.append((i, j))
                unmatched_a.discard(i)
                unmatched_b.discard(j)
        
        # Add unmatched rooms from floor_a as "removed"
        for i in unmatched_a:
            room_a = rooms_a[i]
            room_diffs.append({
                "room_name": room_a.get("name", "Unknown"),
                "room_type": room_a.get("room_type", "unknown"),
                "status": "removed",
                "area_a": room_a.get("area_m2", 0),
                "area_b": None,
                "area_delta_m2": -room_a.get("area_m2", 0),
                "match_score": 0.0,
                "room_a_id": room_a.get("id"),
                "room_b_id": None
            })
        
        # Add unmatched rooms from floor_b as "added"
        for j in unmatched_b:
            room_b = rooms_b[j]
            room_diffs.append({
                "room_name": room_b.get("name", "Unknown"),
                "room_type": room_b.get("room_type", "unknown"),
                "status": "added",
                "area_a": None,
                "area_b": room_b.get("area_m2", 0),
                "area_delta_m2": room_b.get("area_m2", 0),
                "match_score": 0.0,
                "room_a_id": None,
                "room_b_id": room_b.get("id")
            })
        
        # Calculate summary
        summary = self._calculate_summary(room_diffs, floor_a, floor_b)
        
        return {
            "comparison_id": self._generate_comparison_id(),
            "floor_a": {
                "id": floor_a.get("id"),
                "label": floor_a.get("label", "Floor A"),
                "total_area": floor_a.get("total_area_m2", 0),
                "room_count": len(rooms_a),
                "boq_cost": floor_a.get("boq_cost", 0)
            },
            "floor_b": {
                "id": floor_b.get("id"),
                "label": floor_b.get("label", "Floor B"),
                "total_area": floor_b.get("total_area_m2", 0),
                "room_count": len(rooms_b),
                "boq_cost": floor_b.get("boq_cost", 0)
            },
            "room_diffs": room_diffs,
            "summary": summary
        }
    
    def _calculate_match_score(self, room_a: Dict[str, Any], room_b: Dict[str, Any]) -> float:
        """
        Calculate weighted match score between two rooms
        
        Args:
            room_a: First room
            room_b: Second room
            
        Returns:
            Match score between 0.0 and 1.0
        """
        # 1. Name similarity (fuzzy)
        name_score = self._fuzzy_match(
            room_a.get("name", ""),
            room_b.get("name", "")
        )
        
        # 2. Room type match
        type_score = 1.0 if room_a.get("room_type") == room_b.get("room_type") else 0.0
        
        # 3. Area similarity ratio
        area_a = room_a.get("area_m2", 0)
        area_b = room_b.get("area_m2", 0)
        
        if area_a == 0 and area_b == 0:
            area_score = 1.0
        elif area_a == 0 or area_b == 0:
            area_score = 0.0
        else:
            ratio = min(area_a, area_b) / max(area_a, area_b)
            area_score = ratio
        
        # 4. Centroid position similarity
        pos_score = self._position_similarity(room_a, room_b)
        
        # Calculate weighted score
        total_score = (
            (name_score * self.name_weight) +
            (type_score * self.type_weight) +
            (area_score * self.area_weight) +
            (pos_score * self.position_weight)
        )
        
        return round(total_score, 4)
    
    def _fuzzy_match(self, str1: str, str2: str) -> float:
        """
        Calculate fuzzy string similarity
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not str1 or not str2:
            return 0.0
        
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()
        
        if str1 == str2:
            return 1.0
        
        # Simple Levenshtein distance approximation
        len1, len2 = len(str1), len(str2)
        
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Calculate edit distance
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            matrix[i][0] = i
        
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if str1[i - 1] == str2[j - 1] else 1
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j - 1] + cost
                )
        
        distance = matrix[len1][len2]
        max_len = max(len1, len2)
        similarity = 1.0 - (distance / max_len)
        
        return round(similarity, 4)
    
    def _position_similarity(self, room_a: Dict[str, Any], room_b: Dict[str, Any]) -> float:
        """
        Calculate position similarity based on centroid
        
        Args:
            room_a: First room
            room_b: Second room
            
        Returns:
            Position similarity score between 0.0 and 1.0
        """
        # Get centroids
        x_a = room_a.get("x", 0) + room_a.get("width_px", 0) / 2
        y_a = room_a.get("y", 0) + room_a.get("height_px", 0) / 2
        
        x_b = room_b.get("x", 0) + room_b.get("width_px", 0) / 2
        y_b = room_b.get("y", 0) + room_b.get("height_px", 0) / 2
        
        # Calculate distance
        distance = ((x_a - x_b) ** 2 + (y_a - y_b) ** 2) ** 0.5
        
        # Normalize by assuming a typical drawing size of 2000x2000 pixels
        max_distance = 2828  # diagonal of 2000x2000
        similarity = max(0.0, 1.0 - (distance / max_distance))
        
        return round(similarity, 4)
    
    def _calculate_summary(
        self,
        room_diffs: List[Dict[str, Any]],
        floor_a: Dict[str, Any],
        floor_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics for comparison
        
        Args:
            room_diffs: List of room differences
            floor_a: First floor data
            floor_b: Second floor data
            
        Returns:
            Summary statistics
        """
        matched = sum(1 for d in room_diffs if d["status"] == "match")
        changed = sum(1 for d in room_diffs if d["status"] == "changed")
        added = sum(1 for d in room_diffs if d["status"] == "added")
        removed = sum(1 for d in room_diffs if d["status"] == "removed")
        
        area_delta = sum(d.get("area_delta_m2", 0) for d in room_diffs)
        cost_delta = floor_b.get("boq_cost", 0) - floor_a.get("boq_cost", 0)
        
        return {
            "matched": matched,
            "changed": changed,
            "added": added,
            "removed": removed,
            "area_delta_m2": round(area_delta, 2),
            "cost_delta": round(cost_delta, 2)
        }
    
    def _empty_comparison_result(
        self,
        floor_a: Dict[str, Any],
        floor_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return result when both floors are empty"""
        return {
            "comparison_id": self._generate_comparison_id(),
            "floor_a": {
                "id": floor_a.get("id"),
                "label": floor_a.get("label", "Floor A"),
                "total_area": 0,
                "room_count": 0,
                "boq_cost": 0
            },
            "floor_b": {
                "id": floor_b.get("id"),
                "label": floor_b.get("label", "Floor B"),
                "total_area": 0,
                "room_count": 0,
                "boq_cost": 0
            },
            "room_diffs": [],
            "summary": {
                "matched": 0,
                "changed": 0,
                "added": 0,
                "removed": 0,
                "area_delta_m2": 0,
                "cost_delta": 0
            },
            "warning": "Both floors have no detected rooms"
        }
    
    def _all_added_result(
        self,
        floor_a: Dict[str, Any],
        floor_b: Dict[str, Any],
        rooms_b: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Return result when floor_a is empty and floor_b has rooms"""
        room_diffs = []
        total_area_b = 0
        
        for room_b in rooms_b:
            area = room_b.get("area_m2", 0)
            total_area_b += area
            room_diffs.append({
                "room_name": room_b.get("name", "Unknown"),
                "room_type": room_b.get("room_type", "unknown"),
                "status": "added",
                "area_a": None,
                "area_b": area,
                "area_delta_m2": area,
                "match_score": 0.0,
                "room_a_id": None,
                "room_b_id": room_b.get("id")
            })
        
        return {
            "comparison_id": self._generate_comparison_id(),
            "floor_a": {
                "id": floor_a.get("id"),
                "label": floor_a.get("label", "Floor A"),
                "total_area": 0,
                "room_count": 0,
                "boq_cost": 0
            },
            "floor_b": {
                "id": floor_b.get("id"),
                "label": floor_b.get("label", "Floor B"),
                "total_area": total_area_b,
                "room_count": len(rooms_b),
                "boq_cost": floor_b.get("boq_cost", 0)
            },
            "room_diffs": room_diffs,
            "summary": {
                "matched": 0,
                "changed": 0,
                "added": len(rooms_b),
                "removed": 0,
                "area_delta_m2": total_area_b,
                "cost_delta": floor_b.get("boq_cost", 0)
            },
            "warning": f"Floor {floor_a.get('label', 'A')} appears to have no detected rooms"
        }
    
    def _all_removed_result(
        self,
        floor_a: Dict[str, Any],
        floor_b: Dict[str, Any],
        rooms_a: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Return result when floor_b is empty and floor_a has rooms"""
        room_diffs = []
        total_area_a = 0
        
        for room_a in rooms_a:
            area = room_a.get("area_m2", 0)
            total_area_a += area
            room_diffs.append({
                "room_name": room_a.get("name", "Unknown"),
                "room_type": room_a.get("room_type", "unknown"),
                "status": "removed",
                "area_a": area,
                "area_b": None,
                "area_delta_m2": -area,
                "match_score": 0.0,
                "room_a_id": room_a.get("id"),
                "room_b_id": None
            })
        
        return {
            "comparison_id": self._generate_comparison_id(),
            "floor_a": {
                "id": floor_a.get("id"),
                "label": floor_a.get("label", "Floor A"),
                "total_area": total_area_a,
                "room_count": len(rooms_a),
                "boq_cost": floor_a.get("boq_cost", 0)
            },
            "floor_b": {
                "id": floor_b.get("id"),
                "label": floor_b.get("label", "Floor B"),
                "total_area": 0,
                "room_count": 0,
                "boq_cost": 0
            },
            "room_diffs": room_diffs,
            "summary": {
                "matched": 0,
                "changed": 0,
                "added": 0,
                "removed": len(rooms_a),
                "area_delta_m2": -total_area_a,
                "cost_delta": -floor_a.get("boq_cost", 0)
            },
            "warning": f"Floor {floor_b.get('label', 'B')} appears to have no detected rooms"
        }
    
    def _generate_comparison_id(self) -> str:
        """Generate a unique comparison ID"""
        import uuid
        return str(uuid.uuid4())
