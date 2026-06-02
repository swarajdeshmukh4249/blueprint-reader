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
            raise ValueError("GEMINI_API_KEY is not configured")
        
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
        """
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
        
        # Truncate if too many rooms
        if len(parsed_rooms) > MAX_ROOMS_PER_FLOOR:
            notes = data.get("notes", "")
            notes += f" [WARNING: Truncated from {len(parsed_rooms)} to {MAX_ROOMS_PER_FLOOR} rooms]"
            parsed_rooms = parsed_rooms[:MAX_ROOMS_PER_FLOOR]
        else:
            notes = data.get("notes", "")
        
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
        
        # Calculate area
        area_px = width_px * height_px
        
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
