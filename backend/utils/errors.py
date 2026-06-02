"""
Custom exception classes for BlueprintIQ
All errors follow the standard error response contract
"""
from typing import Optional, Dict, Any
import uuid


class BlueprintIQError(Exception):
    """Base exception for all BlueprintIQ errors"""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.error_code = error_code
        self.message = message
        self.field = field
        self.details = details or {}
        self.status_code = status_code
        self.request_id = str(uuid.uuid4())
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to standard error response format"""
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "field": self.field,
            "details": self.details,
            "request_id": self.request_id
        }


# ─── FILE VALIDATION ERRORS ───

class FileValidationError(BlueprintIQError):
    """Base class for file validation errors"""
    def __init__(self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, status_code=400, details=details)


class FileMissingError(FileValidationError):
    def __init__(self):
        super().__init__(
            "FILE_MISSING",
            "No file was provided"
        )


class InvalidFilenameError(FileValidationError):
    def __init__(self, filename: str):
        super().__init__(
            "INVALID_FILENAME",
            f"File '{filename}' has no extension",
            details={"filename": filename}
        )


class UnsupportedFormatError(FileValidationError):
    def __init__(self, filename: str, extension: str):
        from config import SUPPORTED_FILE_TYPES
        super().__init__(
            "UNSUPPORTED_FORMAT",
            f"File format '{extension}' is not supported",
            details={
                "filename": filename,
                "extension": extension,
                "supported_types": SUPPORTED_FILE_TYPES
            }
        )


class FileTooLargeError(FileValidationError):
    def __init__(self, filename: str, size_mb: float):
        from config import MAX_FILE_SIZE_MB
        super().__init__(
            "FILE_TOO_LARGE",
            f"File '{filename}' is too large ({size_mb:.2f}MB)",
            details={
                "filename": filename,
                "max_size_mb": MAX_FILE_SIZE_MB,
                "actual_size_mb": size_mb
            }
        )


class FileCorruptError(FileValidationError):
    def __init__(self, filename: str):
        super().__init__(
            "FILE_CORRUPT",
            f"File '{filename}' is corrupt or unreadable",
            details={"filename": filename}
        )


class EmptyPDFError(FileValidationError):
    def __init__(self, filename: str):
        super().__init__(
            "EMPTY_PDF",
            f"PDF '{filename}' has no pages",
            details={"filename": filename}
        )


class InvalidImageDimensionsError(FileValidationError):
    def __init__(self, filename: str, width: int, height: int):
        super().__init__(
            "INVALID_IMAGE_DIMENSIONS",
            f"Image '{filename}' has invalid dimensions ({width}x{height})",
            details={
                "filename": filename,
                "width": width,
                "height": height
            }
        )


# ─── AI ANALYSIS ERRORS ───

class AIAnalysisError(BlueprintIQError):
    """Base class for AI analysis errors"""
    def __init__(self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, status_code=503, details=details)


class AIEmptyResponseError(AIAnalysisError):
    def __init__(self):
        super().__init__(
            "AI_EMPTY_RESPONSE",
            "AI returned an empty response"
        )


class AIParseError(AIAnalysisError):
    def __init__(self, raw_response: str):
        super().__init__(
            "AI_PARSE_FAILED",
            "Failed to parse AI response as JSON",
            details={"raw_response": raw_response[:500]}  # Truncate for safety
        )


class NoRoomsDetectedError(AIAnalysisError):
    def __init__(self):
        super().__init__(
            "NO_ROOMS_DETECTED",
            "No rooms were detected in the blueprint"
        )


class AIQuotaExceededError(AIAnalysisError):
    def __init__(self):
        super().__init__(
            "AI_QUOTA_EXCEEDED",
            "AI API quota exceeded. Request queued."
        )


class AITimeoutError(AIAnalysisError):
    def __init__(self):
        from config import GEMINI_TIMEOUT_SECONDS
        super().__init__(
            "AI_TIMEOUT",
            f"AI analysis timed out after {GEMINI_TIMEOUT_SECONDS} seconds"
        )


# ─── VALIDATION ERRORS ───

class ValidationError(BlueprintIQError):
    """Base class for validation errors"""
    def __init__(self, error_code: str, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, field=field, status_code=422, details=details)


class RoomNameValidationError(ValidationError):
    def __init__(self, reason: str):
        super().__init__(
            "INVALID_ROOM_NAME",
            reason,
            field="name"
        )


class RoomTypeError(ValidationError):
    def __init__(self, room_type: str):
        from config import ALLOWED_ROOM_TYPES
        super().__init__(
            "INVALID_ROOM_TYPE",
            f"Invalid room type: {room_type}",
            field="room_type",
            details={"allowed_types": ALLOWED_ROOM_TYPES}
        )


class DimensionValidationError(ValidationError):
    def __init__(self, field: str, reason: str):
        super().__init__(
            "INVALID_DIMENSION",
            reason,
            field=field
        )


class FloorValidationError(ValidationError):
    def __init__(self, floor: int):
        from config import MAX_FLOORS
        super().__init__(
            "INVALID_FLOOR",
            f"Floor number out of range (1-{MAX_FLOORS})",
            field="floor",
            details={"floor": floor, "max_floors": MAX_FLOORS}
        )


class UnitValidationError(ValidationError):
    def __init__(self, unit: str):
        from config import SUPPORTED_UNITS
        super().__init__(
            "INVALID_UNIT",
            f"Unsupported unit: {unit}",
            field="unit",
            details={"supported_units": SUPPORTED_UNITS}
        )


# ─── CALIBRATION ERRORS ───

class CalibrationError(BlueprintIQError):
    """Base class for calibration errors"""
    def __init__(self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, status_code=400, details=details)


class CalibrationPointsError(CalibrationError):
    def __init__(self, reason: str):
        super().__init__(
            "CALIBRATION_POINTS_ERROR",
            reason
        )


class CalibrationDistanceError(CalibrationError):
    def __init__(self, reason: str):
        super().__init__(
            "CALIBRATION_DISTANCE_ERROR",
            reason
        )


# ─── COMPARISON ERRORS ───

class ComparisonError(BlueprintIQError):
    """Base class for comparison errors"""
    def __init__(self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, status_code=400, details=details)


class SameFloorError(ComparisonError):
    def __init__(self):
        super().__init__(
            "SAME_FLOOR",
            "Cannot compare a floor with itself"
        )


class FloorNotFoundError(ComparisonError):
    def __init__(self, floor_id: str):
        super().__init__(
            "FLOOR_NOT_FOUND",
            f"Floor {floor_id} not found in this project",
            details={"floor_id": floor_id}
        )


class FloorNotAnalyzedError(ComparisonError):
    def __init__(self, floor_label: str):
        super().__init__(
            "FLOOR_NOT_ANALYZED",
            f"Floor {floor_label} has not been analyzed yet. Run analysis first.",
            details={"floor_label": floor_label}
        )


class FloorNotCalibratedError(ComparisonError):
    def __init__(self, floor_label: str):
        super().__init__(
            "FLOOR_NOT_CALIBRATED",
            f"Floor {floor_label} is not calibrated. Comparison will use pixel dimensions.",
            details={"floor_label": floor_label}
        )


# ─── RESOURCE ERRORS ───

class ResourceNotFoundError(BlueprintIQError):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            "RESOURCE_NOT_FOUND",
            f"{resource_type} with ID '{resource_id}' not found",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ConflictError(BlueprintIQError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            "CONFLICT",
            message,
            status_code=409,
            details=details
        )


class RateLimitError(BlueprintIQError):
    def __init__(self):
        from config import RATE_LIMIT_REQUESTS, RATE_LIMIT_PERIOD_SECONDS
        super().__init__(
            "RATE_LIMIT_EXCEEDED",
            f"Rate limit exceeded: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_PERIOD_SECONDS} seconds",
            status_code=429,
            details={
                "limit": RATE_LIMIT_REQUESTS,
                "period": RATE_LIMIT_PERIOD_SECONDS
            }
        )


class UnauthorizedError(BlueprintIQError):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(
            "UNAUTHORIZED",
            message,
            status_code=401
        )


class ForbiddenError(BlueprintIQError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            "FORBIDDEN",
            message,
            status_code=403
        )
