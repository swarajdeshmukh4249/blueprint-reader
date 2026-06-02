"""
Scale Calibrator Service
Computes scale factor from user-selected points
"""
from typing import Dict, Any, Tuple, Optional, List
import math
from config import (
    MIN_PIXEL_DISTANCE,
    SUPPORTED_UNITS,
    STANDARD_SCALES,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW
)
from utils.errors import (
    CalibrationPointsError,
    CalibrationDistanceError,
    UnitValidationError
)


class ScaleCalibrator:
    """Calculates scale factor from user calibration"""
    
    def __init__(self):
        """Initialize the scale calibrator"""
        self.unit_conversions = {
            "m": 1.0,
            "ft": 0.3048,
            "mm": 0.001,
            "cm": 0.01
        }
    
    def calibrate(
        self,
        pt_a: Tuple[float, float],
        pt_b: Tuple[float, float],
        real_distance: float,
        unit: str
    ) -> Dict[str, Any]:
        """
        Calculate scale factor from two points
        
        Args:
            pt_a: First point [x, y] in canvas pixels
            pt_b: Second point [x, y] in canvas pixels
            real_distance: Real-world distance between points
            unit: Unit of real_distance (m, ft, mm, cm)
            
        Returns:
            Calibration result with scale factor, confidence, and updated rooms
        """
        # 1. Validate points
        if not pt_a or not pt_b:
            raise CalibrationPointsError("Both points are required")
        
        if pt_a == pt_b:
            raise CalibrationPointsError("Points must be different")
        
        # 2. Validate unit
        if unit not in SUPPORTED_UNITS:
            raise UnitValidationError(unit)
        
        # 3. Calculate pixel distance
        pixel_distance = self._calculate_pixel_distance(pt_a, pt_b)
        
        # 4. Validate pixel distance
        if pixel_distance < MIN_PIXEL_DISTANCE:
            raise CalibrationDistanceError(
                f"Pixel distance too small ({pixel_distance:.2f}px). "
                f"Minimum is {MIN_PIXEL_DISTANCE}px"
            )
        
        if pixel_distance > 10000:
            raise CalibrationDistanceError(
                f"Pixel distance too large ({pixel_distance:.2f}px). "
                f"Did you select the right unit?"
            )
        
        # 5. Convert real distance to meters
        real_distance_m = real_distance * self.unit_conversions[unit]
        
        # 6. Calculate scale factor
        scale_factor = real_distance_m / pixel_distance
        
        # 7. Snap to nearest standard scale
        snapped_scale, standard_ratio = self._snap_to_standard_scale(scale_factor)
        
        # 8. Determine confidence based on pixel distance
        confidence = self._determine_confidence(pixel_distance)
        
        # 9. Build result
        result = {
            "pt_a": pt_a,
            "pt_b": pt_b,
            "pixel_distance": pixel_distance,
            "real_distance": real_distance,
            "real_distance_m": real_distance_m,
            "unit": unit,
            "scale_factor": scale_factor,
            "snapped_scale": snapped_scale,
            "standard_ratio": standard_ratio,
            "confidence": confidence,
            "scale_detected": f"1:{int(1/snapped_scale)}" if snapped_scale > 0 else None
        }
        
        return result
    
    def auto_detect_scale(self, image_data: bytes) -> Optional[str]:
        """
        Auto-detect scale from drawing using OCR
        
        Args:
            image_data: Binary image data
            
        Returns:
            Detected scale string (e.g., "1:100") or None
        """
        try:
            import pytesseract
            from PIL import Image
            import io
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Run OCR
            text = pytesseract.image_to_string(image)
            
            # Look for scale patterns
            scale_patterns = [
                r'1[:/]\s*(\d+)',  # 1:100 or 1/100
                r'scale\s*1[:/]\s*(\d+)',  # Scale 1:100
                r'1\s*:\s*(\d+)',  # 1 : 100
            ]
            
            for pattern in scale_patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    scale_value = int(match.group(1))
                    if 10 <= scale_value <= 1000:  # Reasonable scale range
                        return f"1:{scale_value}"
            
            return None
            
        except Exception as e:
            # If OCR fails, return None (will fall back to manual calibration)
            return None
    
    def recalibrate_rooms(
        self,
        rooms: List[Dict[str, Any]],
        old_scale_factor: float,
        new_scale_factor: float
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Recalibrate all rooms with new scale factor
        
        Args:
            rooms: List of rooms with pixel dimensions
            old_scale_factor: Previous scale factor
            new_scale_factor: New scale factor
            
        Returns:
            Tuple of (updated_rooms, diff_summary)
        """
        updated_rooms = []
        diff_summary = {
            "rooms_updated": 0,
            "total_area_delta_m2": 0.0,
            "scale_ratio": new_scale_factor / old_scale_factor
        }
        
        for room in rooms:
            # Get original pixel dimensions
            width_px = room.get("width_px", 0)
            height_px = room.get("height_px", 0)
            
            # Calculate old and new dimensions
            old_width_m = room.get("width_m", 0)
            old_height_m = room.get("height_m", 0)
            old_area_m2 = room.get("area_m2", 0)
            
            new_width_m = width_px * new_scale_factor
            new_height_m = height_px * new_scale_factor
            new_area_m2 = new_width_m * new_height_m
            
            # Update room
            updated_room = room.copy()
            updated_room["width_m"] = new_width_m
            updated_room["height_m"] = new_height_m
            updated_room["area_m2"] = new_area_m2
            updated_room["scale_factor"] = new_scale_factor
            updated_room["needs_calibration"] = False
            
            updated_rooms.append(updated_room)
            
            # Track diff
            diff_summary["rooms_updated"] += 1
            diff_summary["total_area_delta_m2"] += (new_area_m2 - old_area_m2)
        
        return updated_rooms, diff_summary
    
    def _calculate_pixel_distance(self, pt_a: Tuple[float, float], pt_b: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        dx = pt_b[0] - pt_a[0]
        dy = pt_b[1] - pt_a[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def _snap_to_standard_scale(self, scale_factor: float) -> Tuple[float, Optional[float]]:
        """
        Snap scale factor to nearest standard scale
        
        Args:
            scale_factor: Calculated scale factor
            
        Returns:
            Tuple of (snapped_scale, standard_ratio)
        """
        if scale_factor <= 0:
            return scale_factor, None
        
        # Find closest standard scale
        closest_scale = None
        min_diff = float('inf')
        
        for standard in STANDARD_SCALES:
            diff = abs(scale_factor - standard)
            if diff < min_diff:
                min_diff = diff
                closest_scale = standard
        
        if closest_scale is None:
            return scale_factor, None
        
        # Calculate ratio
        standard_ratio = scale_factor / closest_scale if closest_scale > 0 else None
        
        # Only snap if within 20% of standard
        if standard_ratio and 0.8 <= standard_ratio <= 1.2:
            return closest_scale, standard_ratio
        
        return scale_factor, None
    
    def _determine_confidence(self, pixel_distance: float) -> str:
        """
        Determine calibration confidence based on pixel distance
        
        Args:
            pixel_distance: Distance in pixels
            
        Returns:
            Confidence level: "high", "medium", or "low"
        """
        if pixel_distance >= 150:
            return "high"
        elif pixel_distance >= 60:
            return "medium"
        else:
            return "low"
    
    def validate_calibration_request(
        self,
        pt_a: Optional[Tuple[float, float]],
        pt_b: Optional[Tuple[float, float]],
        real_distance: Optional[float],
        unit: Optional[str]
    ) -> Optional[str]:
        """
        Validate calibration request before processing
        
        Args:
            pt_a: First point
            pt_b: Second point
            real_distance: Real-world distance
            unit: Unit of distance
            
        Returns:
            Error message if validation fails, None otherwise
        """
        if not pt_a or not pt_b:
            return "Both points are required"
        
        if pt_a == pt_b:
            return "Points must be different"
        
        if not unit or unit not in SUPPORTED_UNITS:
            return f"Unsupported unit. Use: {', '.join(SUPPORTED_UNITS)}"
        
        if real_distance is None or real_distance <= 0:
            return "Real distance must be greater than 0"
        
        pixel_distance = self._calculate_pixel_distance(pt_a, pt_b)
        
        if pixel_distance < MIN_PIXEL_DISTANCE:
            return f"Pixel distance too small ({pixel_distance:.2f}px). Minimum is {MIN_PIXEL_DISTANCE}px"
        
        if pixel_distance > 10000:
            return "Pixel distance too large. Did you select the right unit?"
        
        return None
