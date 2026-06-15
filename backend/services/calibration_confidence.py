"""
Calibration Confidence System
Calculates confidence scores for manual scale calibrations based on multiple factors.
"""

from typing import Optional, Dict, Any
from enum import Enum

class ConfidenceLevel(Enum):
    """Confidence level categories"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"

class ReferenceType(Enum):
    """Types of calibration references"""
    DIMENSION_LINE = "dimension_line"  # CAD dimension line (most reliable)
    KNOWN_OBJECT = "known_object"      # Object with known size (door, window)
    GRID = "grid"                      # Grid lines
    MANUAL = "manual"                  # User-provided without reference
    ESTIMATED = "estimated"            # Estimated from context

class CalibrationConfidenceService:
    """Service for calculating calibration confidence scores"""
    
    # Confidence thresholds
    HIGH_THRESHOLD = 0.85
    MEDIUM_THRESHOLD = 0.60
    LOW_THRESHOLD = 0.40
    
    # Reference type weights
    REFERENCE_WEIGHTS = {
        ReferenceType.DIMENSION_LINE: 1.0,
        ReferenceType.KNOWN_OBJECT: 0.85,
        ReferenceType.GRID: 0.70,
        ReferenceType.MANUAL: 0.50,
        ReferenceType.ESTIMATED: 0.30,
    }
    
    # Known object standard sizes (in feet) for validation
    KNOWN_OBJECT_SIZES = {
        "door": 3.0,      # Standard door width
        "window": 3.0,    # Standard window width
        "door_height": 7.0,  # Standard door height
        "standard_room": 12.0,  # Typical room dimension
    }
    
    @staticmethod
    def calculate_confidence(
        point1_x: float,
        point1_y: float,
        point2_x: float,
        point2_y: float,
        known_distance: float,
        known_unit: str,
        reference_type: str = "manual",
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate confidence score for a manual scale calibration.
        
        Args:
            point1_x, point1_y: First calibration point coordinates
            point2_x, point2_y: Second calibration point coordinates
            known_distance: Known distance between points
            known_unit: Unit of known distance (ft, m, in, etc.)
            reference_type: Type of reference used for calibration
            additional_context: Additional context information
            
        Returns:
            Dictionary with confidence score, level, warnings, and badge info
        """
        context = additional_context or {}
        
        # Calculate pixel distance
        pixel_distance = ((point2_x - point1_x) ** 2 + (point2_y - point1_y) ** 2) ** 0.5
        
        # Base confidence from reference type
        try:
            ref_type = ReferenceType(reference_type)
            base_confidence = CalibrationConfidenceService.REFERENCE_WEIGHTS[ref_type]
        except ValueError:
            base_confidence = CalibrationConfidenceService.REFERENCE_WEIGHTS[ReferenceType.MANUAL]
        
        # Factor 1: Distance between points (longer distances = higher confidence)
        distance_factor = CalibrationConfidenceService._calculate_distance_factor(pixel_distance)
        
        # Factor 2: Known distance reasonableness
        distance_reasonableness = CalibrationConfidenceService._calculate_distance_reasonableness(
            known_distance, known_unit
        )
        
        # Factor 3: Reference type validation
        reference_validation = CalibrationConfidenceService._validate_reference_type(
            reference_type, known_distance, known_unit, context
        )
        
        # Factor 4: Consistency with existing calibrations (if provided)
        consistency_factor = CalibrationConfidenceService._calculate_consistency(
            context.get('existing_calibrations', []),
            pixel_distance,
            known_distance
        )
        
        # Calculate final confidence score
        confidence_score = (
            base_confidence * 0.4 +
            distance_factor * 0.2 +
            distance_reasonableness * 0.15 +
            reference_validation * 0.15 +
            consistency_factor * 0.1
        )
        
        # Clamp to 0-1 range
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        # Determine confidence level
        confidence_level = CalibrationConfidenceService._get_confidence_level(confidence_score)
        
        # Generate warnings
        warnings = CalibrationConfidenceService._generate_warnings(
            confidence_score,
            confidence_level,
            pixel_distance,
            known_distance,
            reference_type
        )
        
        # Generate badge info
        badge = CalibrationConfidenceService._generate_badge(confidence_level, confidence_score)
        
        return {
            "confidence_score": round(confidence_score, 3),
            "confidence_level": confidence_level.value,
            "badge": badge,
            "warnings": warnings,
            "factors": {
                "reference_type_weight": round(base_confidence, 3),
                "distance_factor": round(distance_factor, 3),
                "distance_reasonableness": round(distance_reasonableness, 3),
                "reference_validation": round(reference_validation, 3),
                "consistency_factor": round(consistency_factor, 3),
            },
            "calculated_scale": round(pixel_distance / known_distance, 6) if known_distance > 0 else None,
            "pixel_distance": round(pixel_distance, 2),
        }
    
    @staticmethod
    def _calculate_distance_factor(pixel_distance: float) -> float:
        """Calculate confidence factor based on pixel distance between points."""
        # Longer distances are more reliable for calibration
        # Minimum 50 pixels, optimal 500+ pixels
        if pixel_distance < 50:
            return 0.3  # Too short
        elif pixel_distance < 100:
            return 0.5  # Short
        elif pixel_distance < 300:
            return 0.8  # Good
        else:
            return 1.0  # Excellent
    
    @staticmethod
    def _calculate_distance_reasonableness(known_distance: float, known_unit: str) -> float:
        """Calculate confidence factor based on reasonableness of known distance."""
        # Convert to feet for standardization
        distance_ft = CalibrationConfidenceService._convert_to_feet(known_distance, known_unit)
        
        # Check if distance is reasonable for architectural drawings
        # Typical calibration distances: 1 ft to 100 ft
        if distance_ft < 0.1 or distance_ft > 500:
            return 0.2  # Unreasonable
        elif distance_ft < 0.5 or distance_ft > 200:
            return 0.5  # Questionable
        elif distance_ft < 1 or distance_ft > 100:
            return 0.8  # Reasonable
        else:
            return 1.0  # Excellent
    
    @staticmethod
    def _validate_reference_type(
        reference_type: str,
        known_distance: float,
        known_unit: str,
        context: Dict[str, Any]
    ) -> float:
        """Validate reference type against known object sizes if applicable."""
        distance_ft = CalibrationConfidenceService._convert_to_feet(known_distance, known_unit)
        
        if reference_type == "known_object":
            object_type = context.get("object_type", "").lower()
            if object_type in CalibrationConfidenceService.KNOWN_OBJECT_SIZES:
                expected_size = CalibrationConfidenceService.KNOWN_OBJECT_SIZES[object_type]
                # Allow 20% tolerance
                tolerance = expected_size * 0.2
                if abs(distance_ft - expected_size) <= tolerance:
                    return 1.0  # Matches known object size
                else:
                    return 0.5  # Doesn't match expected size
            else:
                return 0.7  # Unknown object type
        
        return 1.0  # No validation for other reference types
    
    @staticmethod
    def _calculate_consistency(
        existing_calibrations: list,
        pixel_distance: float,
        known_distance: float
    ) -> float:
        """Calculate consistency factor with existing calibrations."""
        if not existing_calibrations:
            return 1.0  # No existing calibrations to compare
        
        # Calculate scale from this calibration
        new_scale = pixel_distance / known_distance if known_distance > 0 else 0
        
        if new_scale == 0:
            return 0.0
        
        # Compare with existing scales
        scales = []
        for cal in existing_calibrations:
            if cal.get("calculated_scale"):
                scales.append(cal["calculated_scale"])
        
        if not scales:
            return 1.0
        
        # Calculate average deviation
        avg_scale = sum(scales) / len(scales)
        deviation = abs(new_scale - avg_scale) / avg_scale if avg_scale > 0 else 1.0
        
        # Lower deviation = higher consistency
        if deviation < 0.05:
            return 1.0  # Very consistent
        elif deviation < 0.1:
            return 0.8  # Consistent
        elif deviation < 0.2:
            return 0.5  # Somewhat consistent
        else:
            return 0.2  # Inconsistent
    
    @staticmethod
    def _get_confidence_level(confidence_score: float) -> ConfidenceLevel:
        """Determine confidence level from score."""
        if confidence_score >= CalibrationConfidenceService.HIGH_THRESHOLD:
            return ConfidenceLevel.HIGH
        elif confidence_score >= CalibrationConfidenceService.MEDIUM_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= CalibrationConfidenceService.LOW_THRESHOLD:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    @staticmethod
    def _generate_warnings(
        confidence_score: float,
        confidence_level: ConfidenceLevel,
        pixel_distance: float,
        known_distance: float,
        reference_type: str
    ) -> list:
        """Generate warnings based on confidence factors."""
        warnings = []
        
        if confidence_level == ConfidenceLevel.VERY_LOW:
            warnings.append({
                "type": "critical",
                "message": "Calibration confidence is very low. Results may be inaccurate."
            })
        elif confidence_level == ConfidenceLevel.LOW:
            warnings.append({
                "type": "warning",
                "message": "Calibration confidence is low. Consider using a more reliable reference."
            })
        
        if pixel_distance < 50:
            warnings.append({
                "type": "info",
                "message": "Calibration points are very close together. Use points further apart for better accuracy."
            })
        
        if reference_type == "manual":
            warnings.append({
                "type": "info",
                "message": "Manual calibration without reference. Consider using dimension lines or known objects for higher confidence."
            })
        
        if known_distance < 0.1 or known_distance > 200:
            warnings.append({
                "type": "warning",
                "message": "Known distance is unusual for architectural drawings. Verify the value is correct."
            })
        
        return warnings
    
    @staticmethod
    def _generate_badge(confidence_level: ConfidenceLevel, confidence_score: float) -> Dict[str, Any]:
        """Generate badge information for UI display."""
        badge_colors = {
            ConfidenceLevel.HIGH: "#10B981",      # Green
            ConfidenceLevel.MEDIUM: "#F59E0B",    # Amber
            ConfidenceLevel.LOW: "#EF4444",       # Red
            ConfidenceLevel.VERY_LOW: "#7C3AED",  # Purple
        }
        
        badge_labels = {
            ConfidenceLevel.HIGH: "High Confidence",
            ConfidenceLevel.MEDIUM: "Medium Confidence",
            ConfidenceLevel.LOW: "Low Confidence",
            ConfidenceLevel.VERY_LOW: "Very Low Confidence",
        }
        
        return {
            "level": confidence_level.value,
            "label": badge_labels[confidence_level],
            "color": badge_colors[confidence_level],
            "score": round(confidence_score * 100, 1),
            "icon": CalibrationConfidenceService._get_badge_icon(confidence_level)
        }
    
    @staticmethod
    def _get_badge_icon(confidence_level: ConfidenceLevel) -> str:
        """Get icon name for confidence level."""
        icons = {
            ConfidenceLevel.HIGH: "check-circle",
            ConfidenceLevel.MEDIUM: "alert-circle",
            ConfidenceLevel.LOW: "warning-circle",
            ConfidenceLevel.VERY_LOW: "x-circle",
        }
        return icons[confidence_level]
    
    @staticmethod
    def _convert_to_feet(distance: float, unit: str) -> float:
        """Convert distance to feet for standardization."""
        unit = unit.lower()
        conversions = {
            "ft": 1.0,
            "feet": 1.0,
            "m": 3.28084,
            "meter": 3.28084,
            "meters": 3.28084,
            "in": 1.0 / 12.0,
            "inch": 1.0 / 12.0,
            "inches": 1.0 / 12.0,
            "mm": 1.0 / 304.8,
            "cm": 1.0 / 30.48,
        }
        return distance * conversions.get(unit, 1.0)
