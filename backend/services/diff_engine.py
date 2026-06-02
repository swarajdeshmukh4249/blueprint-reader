from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher
import uuid

class Room:
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.name = data.get('name')
        self.room_type = data.get('room_type')
        self.area_sqft = data.get('area_sqft')
        self.width_ft = data.get('width_ft')
        self.height_ft = data.get('height_ft')
        self.polygon_coordinates = data.get('polygon_coordinates')
        self.centroid_x = data.get('centroid_x')
        self.centroid_y = data.get('centroid_y')
        self.is_deleted = data.get('is_deleted', False)

class VersionDiff:
    def __init__(self, version1: dict, version2: dict):
        self.version1 = version1
        self.version2 = version2
        self.changes = {
            "added": [],
            "removed": [],
            "modified": [],
            "unchanged": []
        }
        self.area_difference = 0
        self.cost_difference = 0
        self.summary = ""

class DiffEngine:
    def compare_versions(
        self,
        version1_data: dict,
        version2_data: dict
    ) -> VersionDiff:
        """Compare two analysis versions"""
        
        v1_rooms = [Room(r) for r in version1_data.get('rooms', [])]
        v2_rooms = [Room(r) for r in version2_data.get('rooms', [])]
        
        diff = VersionDiff(version1_data, version2_data)
        
        # Match rooms between versions
        room_pairs = self._match_rooms(v1_rooms, v2_rooms)
        
        for r1, r2 in room_pairs:
            if r1 is None:
                diff.changes["added"].append(r2)
            elif r2 is None:
                diff.changes["removed"].append(r1)
            elif self._rooms_differ(r1, r2):
                diff.changes["modified"].append({
                    "old": r1,
                    "new": r2,
                    "changes": self._get_room_changes(r1, r2)
                })
            else:
                diff.changes["unchanged"].append(r1)
        
        # Calculate area difference
        v1_area = sum(r.area_sqft for r in v1_rooms if r.area_sqft)
        v2_area = sum(r.area_sqft for r in v2_rooms if r.area_sqft)
        diff.area_difference = v2_area - v1_area
        
        # Calculate cost difference (simplified)
        v1_cost = version1_data.get('total_cost', 0)
        v2_cost = version2_data.get('total_cost', 0)
        diff.cost_difference = v2_cost - v1_cost
        
        # Generate summary
        diff.summary = self._generate_diff_summary(diff)
        
        return diff
    
    def _match_rooms(
        self,
        rooms1: List[Room],
        rooms2: List[Room]
    ) -> List[Tuple[Optional[Room], Optional[Room]]]:
        """Match rooms between versions using similarity scoring"""
        pairs = []
        used2 = set()
        
        for r1 in rooms1:
            best_match = None
            best_score = 0
            
            for i, r2 in enumerate(rooms2):
                if i in used2:
                    continue
                
                score = self._calculate_room_similarity(r1, r2)
                if score > best_score and score > 0.7:  # 70% similarity threshold
                    best_match = (i, r2)
                    best_score = score
            
            if best_match:
                idx, r2 = best_match
                pairs.append((r1, r2))
                used2.add(idx)
            else:
                pairs.append((r1, None))
        
        # Add unmatched rooms from version 2
        for i, r2 in enumerate(rooms2):
            if i not in used2:
                pairs.append((None, r2))
        
        return pairs
    
    def _calculate_room_similarity(self, r1: Room, r2: Room) -> float:
        """Calculate similarity score between two rooms"""
        # Name similarity
        name_sim = SequenceMatcher(None, r1.name.lower(), r2.name.lower()).ratio()
        
        # Position similarity (centroid distance)
        if r1.centroid_x and r1.centroid_y and r2.centroid_x and r2.centroid_y:
            dist = ((r1.centroid_x - r2.centroid_x)**2 + (r1.centroid_y - r2.centroid_y)**2)**0.5
            pos_sim = max(0, 1 - dist / 1000)  # Normalize
        else:
            pos_sim = 0.5
        
        # Area similarity
        if r1.area_sqft and r2.area_sqft:
            area_sim = 1 - abs(r1.area_sqft - r2.area_sqft) / max(r1.area_sqft, r2.area_sqft)
        else:
            area_sim = 0.5
        
        # Weighted average
        return (name_sim * 0.4 + pos_sim * 0.3 + area_sim * 0.3)
    
    def _rooms_differ(self, r1: Room, r2: Room) -> bool:
        """Check if two rooms differ significantly"""
        if r1.name != r2.name:
            return True
        if r1.area_sqft and r2.area_sqft and abs(r1.area_sqft - r2.area_sqft) > 10:
            return True
        if r1.polygon_coordinates != r2.polygon_coordinates:
            return True
        return False
    
    def _get_room_changes(self, r1: Room, r2: Room) -> Dict[str, Any]:
        """Get specific changes between room versions"""
        changes = {}
        
        if r1.name != r2.name:
            changes["name"] = {"old": r1.name, "new": r2.name}
        
        if r1.area_sqft and r2.area_sqft and r1.area_sqft != r2.area_sqft:
            changes["area"] = {
                "old": r1.area_sqft,
                "new": r2.area_sqft,
                "diff": r2.area_sqft - r1.area_sqft
            }
        
        if r1.polygon_coordinates != r2.polygon_coordinates:
            changes["geometry"] = "modified"
        
        return changes
    
    def _generate_diff_summary(self, diff: VersionDiff) -> str:
        """Generate human-readable diff summary"""
        added = len(diff.changes["added"])
        removed = len(diff.changes["removed"])
        modified = len(diff.changes["modified"])
        
        parts = []
        if added > 0:
            parts.append(f"{added} room{'s' if added > 1 else ''} added")
        if removed > 0:
            parts.append(f"{removed} room{'s' if removed > 1 else ''} removed")
        if modified > 0:
            parts.append(f"{modified} room{'s' if modified > 1 else ''} modified")
        
        if not parts:
            return "No changes detected"
        
        summary = ", ".join(parts)
        
        if diff.area_difference != 0:
            area_change = abs(diff.area_difference)
            direction = "increased" if diff.area_difference > 0 else "decreased"
            summary += f". Total area {direction} by {area_change:.2f} sq ft"
        
        return summary
