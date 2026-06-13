"""
Vision Analyzer Service
Handles Gemini API calls with defensive response parsing
"""
import json
import re
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL_FAST,
    GEMINI_MODEL_ACCURATE,
    GEMINI_MAX_RETRIES,
    GEMINI_TIMEOUT_SECONDS,
    ALLOWED_ROOM_TYPES,
    MAX_ROOMS_PER_FLOOR,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW
)
from utils.errors import (
    AIEmptyResponseError,
    AIParseError,
    NoRoomsDetectedError,
    AIQuotaExceededError,
    AITimeoutError
)


class VisionAnalyzer:
    """Analyzes blueprint images using Google Gemini Vision API"""
    
    def __init__(self, use_fast_model: bool = True):
        """Initialize the vision analyzer"""
        if not GEMINI_API_KEY:
            self.model = None
            self.model_name = None
            return

        genai.configure(api_key=GEMINI_API_KEY)
        self.model_name = GEMINI_MODEL_FAST if use_fast_model else GEMINI_MODEL_ACCURATE
        self.model = genai.GenerativeModel(self.model_name)
    
    def analyze_blueprint(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Analyze a blueprint image and extract room information

        Args:
            image_data: Binary image data
            filename: Name of the file being analyzed

        Returns:
            Parsed analysis result with rooms and metadata or error code

        Error codes:
            "AI_EMPTY_RESPONSE": If Gemini returns empty response
            "AI_PARSE_FAILED": If response cannot be parsed as JSON
            "NO_ROOMS_DETECTED": If no rooms are detected
            "AI_QUOTA_EXCEEDED": If API quota is exceeded
            "AI_TIMEOUT": If request times out
            "AI_NOT_CONFIGURED": If GEMINI_API_KEY is not configured
        """
        # Check if model is initialized (API key configured)
        if not self.model:
            return {
                "error_code": "AI_NOT_CONFIGURED",
                "error_message": "GEMINI_API_KEY is not configured. Please set the environment variable.",
                "filename": filename,
                "rooms": [],
                "total_area_px": 0,
                "drawing_type": "unknown",
                "scale_detected": None,
                "notes": "AI analysis not available - API key not configured"
            }

        # Prepare the prompt
        prompt = self._build_analysis_prompt()

        # Retry logic
        for attempt in range(GEMINI_MAX_RETRIES):
            try:
                # Call Gemini API
                response = self.model.generate_content(
                    [prompt, {"mime_type": "image/png", "data": image_data}],
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=4096,
                    )
                )

                # Get response text
                response_text = response.text

                # Parse response
                result = self._parse_response(response_text, filename)

                # If result has error_code for AI_EMPTY_RESPONSE, retry once
                if result.get("error_code") == "AI_EMPTY_RESPONSE" and attempt == 0:
                    continue

                return result

            except Exception as e:
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    return {
                        "error_code": "AI_QUOTA_EXCEEDED",
                        "error_message": "Gemini API quota exceeded",
                        "filename": filename
                    }
                elif "timeout" in str(e).lower():
                    return {
                        "error_code": "AI_TIMEOUT",
                        "error_message": "Gemini API request timed out",
                        "filename": filename
                    }
                elif attempt == GEMINI_MAX_RETRIES - 1:
                    # Last attempt failed
                    return {
                        "error_code": "AI_PARSE_FAILED",
                        "error_message": f"Failed to parse Gemini response: {str(e)}",
                        "filename": filename
                    }

        # Should not reach here, but just in case
        return {
            "error_code": "AI_TIMEOUT",
            "error_message": "Gemini API request timed out",
            "filename": filename
        }
    
    def _build_analysis_prompt(self) -> str:
        """Build the analysis prompt for Gemini"""
        return """
You are an expert blueprint analyzer. Analyze this architectural blueprint and extract room information.

Return ONLY a valid JSON object with this exact structure:
{
  "rooms": [
    {
      "name": str,
      "room_type": str,
      "width_px": float,
      "height_px": float,
      "floor": int,
      "confidence": float,
      "wall_type": str,
      "x": float,
      "y": float
    }
  ],
  "drawing_type": str,
  "total_area_px": float,
  "scale_detected": str|null,
  "notes": str
}

Rules:
- room_type must be one of: bedroom, bathroom, kitchen, living_room, dining_room, corridor, balcony, store, utility, parking, lobby, office, staircase, lift, terrace, unknown
- confidence must be between 0.0 and 1.0
- floor should be 1-indexed (1 for ground floor)
- width_px and height_px are in pixels
- x and y are the top-left coordinates of the room bounding box
- wall_type should be: load_bearing, partition, external, or unknown
- scale_detected should be in format "1:100" or null if not detected
- Return ONLY the JSON, no markdown code fences, no explanations
"""
    
    def _parse_response(self, response_text: str, filename: str) -> Dict[str, Any]:
        """
        Parse Gemini response defensively
        
        Args:
            response_text: Raw response text from Gemini
            filename: Name of the file being analyzed
            
        Returns:
            Parsed analysis result with safe defaults or error code
            
        Error codes:
            "AI_EMPTY_RESPONSE": If response is empty
            "AI_PARSE_FAILED": If response cannot be parsed as JSON
            "NO_ROOMS_DETECTED": If no rooms are detected (still returns partial result)
        """
        # 1. Check for empty response
        if not response_text or response_text.strip() == "":
            return {
                "error_code": "AI_EMPTY_RESPONSE",
                "error_message": "Gemini returned empty response",
                "filename": filename
            }
        
        # 2. Strip markdown fences if present
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            cleaned_text = re.sub(r'^```(?:json)?\n', '', cleaned_text)
            cleaned_text = re.sub(r'\n```$', '', cleaned_text)
        
        # 3. Try to parse JSON
        try:
            data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            return {
                "error_code": "AI_PARSE_FAILED",
                "error_message": "Failed to parse Gemini response as JSON",
                "filename": filename,
                "raw_response": response_text[:500]  # First 500 chars for debugging
            }
        
        # 4. Validate and parse rooms with safe defaults
        rooms = data.get("rooms", [])
        
        if not rooms:
            # Return partial result with error code
            return {
                "error_code": "NO_ROOMS_DETECTED",
                "error_message": "No rooms detected in blueprint",
                "rooms": [],
                "drawing_type": data.get("drawing_type", "unknown"),
                "total_area_px": data.get("total_area_px", 0.0),
                "scale_detected": data.get("scale_detected", None),
                "notes": data.get("notes", ""),
                "filename": filename
            }
        
        # Process each room with defensive parsing
        parsed_rooms = []
        for i, room in enumerate(rooms):
            parsed_room = self._parse_room(room, i)
            parsed_rooms.append(parsed_room)

        # Detect plan boundaries for multi-floor files
        plan_clusters = self._detect_plan_boundaries(parsed_rooms)

        # Assign floor numbers based on plan clusters
        if len(plan_clusters) > 1:
            notes = data.get("notes", "")
            notes += f" [INFO: Detected {len(plan_clusters)} separate floor plans]"
            for floor_idx, cluster in enumerate(plan_clusters):
                for room in cluster:
                    room["floor"] = floor_idx + 1
            # Flatten clusters back to single list
            parsed_rooms = [room for cluster in plan_clusters for room in cluster]
        else:
            notes = data.get("notes", "")

        # Truncate if too many rooms
        if len(parsed_rooms) > MAX_ROOMS_PER_FLOOR:
            notes += f" [WARNING: Truncated from {len(parsed_rooms)} to {MAX_ROOMS_PER_FLOOR} rooms]"
            parsed_rooms = parsed_rooms[:MAX_ROOMS_PER_FLOOR]
        
        # 5. Build result with safe defaults
        result = {
            "rooms": parsed_rooms,
            "drawing_type": data.get("drawing_type", "unknown"),
            "total_area_px": data.get("total_area_px", sum(r["width_px"] * r["height_px"] for r in parsed_rooms)),
            "scale_detected": data.get("scale_detected", None),
            "notes": notes,
            "filename": filename
        }
        
        return result
    
    def _parse_room(self, room: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Parse a single room with safe defaults

        Args:
            room: Raw room data from Gemini
            index: Index of the room (for default naming)

        Returns:
            Parsed room data with safe defaults
        """
        # Name - default to "Unknown Room {n}" if missing
        name = room.get("name")
        if not name or name.strip() == "":
            name = f"Unknown Room {index + 1}"

        # Room type - default to "unknown" if not in allowed list
        room_type_raw = room.get("room_type", "unknown")
        room_type = room_type_raw.lower() if room_type_raw else "unknown"
        needs_review = False
        if room_type not in ALLOWED_ROOM_TYPES:
            room_type = "unknown"
            needs_review = True

        # Width - default to 0.0 if missing or non-numeric
        try:
            width_px = float(room.get("width_px", 0))
        except (ValueError, TypeError):
            width_px = 0.0

        # Height - default to 0.0 if missing or non-numeric
        try:
            height_px = float(room.get("height_px", 0))
        except (ValueError, TypeError):
            height_px = 0.0

        # Floor - default to 1 if missing
        try:
            floor = int(room.get("floor", 1))
        except (ValueError, TypeError):
            floor = 1

        # Confidence - default to 0.0 if missing, clamp to 0.0-1.0
        try:
            confidence = float(room.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.0

        # Wall type - default to "unknown"
        wall_type = room.get("wall_type", "unknown").lower()
        if wall_type not in ["load_bearing", "partition", "external"]:
            wall_type = "unknown"

        # X and Y coordinates - default to 0
        try:
            x = float(room.get("x", 0))
        except (ValueError, TypeError):
            x = 0.0

        try:
            y = float(room.get("y", 0))
        except (ValueError, TypeError):
            y = 0.0

        # Handle negative dimensions
        width_px = abs(width_px)
        height_px = abs(height_px)

        # Flag for calibration if dimensions are 0
        needs_calibration = width_px == 0 or height_px == 0

        # Calculate area from pixels
        area_px = width_px * height_px

        # Try to parse room area from name label (e.g., "KITCHEN 10'X10'2''")
        area_from_label = self._parse_room_area_from_label(name)
        if area_from_label:
            area_px = area_from_label  # Use parsed area if available

        # Check for unrealistic room (larger than total area would indicate)
        # This will be checked at a higher level when we have total_area_px

        return {
            "name": name,
            "room_type": room_type,
            "width_px": width_px,
            "height_px": height_px,
            "floor": floor,
            "confidence": confidence,
            "wall_type": wall_type,
            "x": x,
            "y": y,
            "area_px": area_px,
            "needs_calibration": needs_calibration,
            "needs_review": needs_review,
            "source": "ai_detected"
        }

    def _parse_room_area_from_label(self, label_text: str) -> Optional[float]:
        """
        Parse room area from label text using dimension pattern

        Args:
            label_text: Room label text (e.g., "KITCHEN 10'X10'2''" or "MASTER BEDROOM-1 13'2''X10''")

        Returns:
            Area in square feet if dimensions found, None otherwise
        """
        # Pattern for dimensions like: 10'X10'2'' or 13'2''X10''
        match = re.search(r"(\d+)'(\d+)?''?\s*[Xx]\s*(\d+)'(\d+)?''?", label_text)
        if match:
            try:
                ft1 = int(match.group(1))
                in1 = int(match.group(2)) if match.group(2) else 0
                ft2 = int(match.group(3))
                in2 = int(match.group(4)) if match.group(4) else 0
                dim1 = ft1 + in1 / 12
                dim2 = ft2 + in2 / 12
                return round(dim1 * dim2, 2)
            except (ValueError, IndexError):
                pass
        return None

    def _detect_plan_boundaries(self, rooms: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Detect plan boundaries by clustering rooms based on spatial position

        Args:
            rooms: List of room dictionaries with x, y coordinates

        Returns:
            List of room clusters, where each cluster represents a separate floor/plan
        """
        if not rooms:
            return []

        # Extract X coordinates
        x_coords = [room.get("x", 0) for room in rooms]
        if not x_coords:
            return [rooms]

        # Find gaps in X coordinates to separate plans
        x_coords_sorted = sorted(x_coords)
        gaps = []
        for i in range(1, len(x_coords_sorted)):
            gap = x_coords_sorted[i] - x_coords_sorted[i-1]
            if gap > 100:  # Threshold for plan separation (adjust as needed)
                gaps.append(gap)

        # If no significant gaps, treat as single plan
        if not gaps:
            return [rooms]

        # Use the largest gap to split plans
        max_gap = max(gaps)
        threshold = x_coords_sorted[x_coords_sorted.index(max_gap) - 1] + max_gap / 2

        # Split rooms into clusters based on threshold
        plan1 = [room for room in rooms if room.get("x", 0) < threshold]
        plan2 = [room for room in rooms if room.get("x", 0) >= threshold]

        # Recursively check for more plans
        result = []
        if plan1:
            result.extend(self._detect_plan_boundaries(plan1))
        if plan2:
            result.extend(self._detect_plan_boundaries(plan2))

        return result
