"""
Multi-Provider Vision Analyzer
Supports multiple AI providers with automatic fallback
"""
import base64
import re
from typing import Dict, Any, List, Optional
from config import (
    OPENAI_API_KEY, GROQ_API_KEY, GEMINI_API_KEY,
    OPENAI_MODEL_FAST, GROQ_MODEL_FAST, GEMINI_MODEL_FAST,
    OPENAI_MAX_RETRIES, GROQ_MAX_RETRIES, GEMINI_MAX_RETRIES,
    AI_PROVIDERS
)

try:
    from openai import OpenAI as OpenAIClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from groq import Groq as GroqClient
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class MultiProviderAnalyzer:
    """
    Multi-provider vision analyzer with automatic fallback
    Tries providers in order defined by AI_PROVIDERS config
    """

    def __init__(self, use_fast_model: bool = True):
        self.use_fast_model = use_fast_model
        self.openai_client = None
        self.groq_client = None
        self.gemini_model = None

        # Initialize OpenAI client if API key is available
        if OPENAI_AVAILABLE and OPENAI_API_KEY:
            try:
                self.openai_client = OpenAIClient(api_key=OPENAI_API_KEY)
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")

        # Initialize Groq client if API key is available
        if GROQ_AVAILABLE and GROQ_API_KEY:
            try:
                self.groq_client = GroqClient(api_key=GROQ_API_KEY)
            except Exception as e:
                print(f"Failed to initialize Groq client: {e}")

        # Initialize Gemini model if API key is available
        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # Use vision-enabled model
                model_name = GEMINI_MODEL_FAST if use_fast_model else GEMINI_MODEL_ACCURATE
                self.gemini_model = genai.GenerativeModel(model_name)
            except Exception as e:
                print(f"Failed to initialize Gemini model: {e}")
                self.gemini_model = None

    def _build_analysis_prompt(self) -> str:
        """Build the analysis prompt for blueprint analysis"""
        return """
You are an expert architectural blueprint analyzer. Analyze this blueprint image and extract detailed room information.

Return a JSON response with this exact structure:
{
  "rooms": [
    {
      "name": "Room name (e.g., MASTER BEDROOM)",
      "type": "room type (e.g., bedroom, bathroom, kitchen)",
      "x": x_coordinate_in_pixels,
      "y": y_coordinate_in_pixels,
      "width": width_in_pixels,
      "height": height_in_pixels,
      "area_px": area_in_square_pixels,
      "area_ft": estimated_area_in_square_feet,
      "confidence": confidence_score_0_to_1,
      "notes": "any additional observations"
    }
  ],
  "drawing_type": "type of drawing (floor_plan, elevation, section)",
  "scale_detected": "scale if detectable (e.g., 1:100)",
  "total_area_px": total_area_in_square_pixels,
  "notes": "general observations about the blueprint"
}

Important:
- Extract ALL rooms visible in the blueprint
- Provide accurate pixel coordinates and dimensions
- Estimate areas in square feet based on typical room scales
- Include confidence scores for each detection
- If you see multiple floor plans in one image, extract all rooms from all plans
"""

    def _encode_image(self, image_data: bytes) -> str:
        """Encode image data to base64"""
        return base64.b64encode(image_data).decode('utf-8')

    def _parse_room_area_from_label(self, label_text: str) -> Optional[float]:
        """Parse room area from label text using dimension pattern"""
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

    def _analyze_with_openai(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        """Analyze blueprint using OpenAI"""
        if not self.openai_client:
            return {
                "error_code": "OPENAI_NOT_CONFIGURED",
                "error_message": "OpenAI client not initialized. Check OPENAI_API_KEY.",
                "filename": filename,
                "rooms": [],
                "total_area_px": 0,
                "drawing_type": "unknown",
                "scale_detected": None,
                "notes": "OpenAI not available"
            }

        try:
            prompt = self._build_analysis_prompt()
            base64_image = self._encode_image(image_data)

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
            )

            response_text = response.choices[0].message.content
            return self._parse_response(response_text, filename)

        except Exception as e:
            return {
                "error_code": "OPENAI_API_ERROR",
                "error_message": str(e),
                "filename": filename,
                "rooms": [],
                "total_area_px": 0,
                "drawing_type": "unknown",
                "scale_detected": None,
                "notes": f"OpenAI error: {str(e)}"
            }

    def _detect_plan_boundaries(self, rooms: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Detect plan boundaries by clustering rooms based on spatial position"""
        if not rooms:
            return []

        x_coords = [room.get("x", 0) for room in rooms]
        if not x_coords:
            return [rooms]

        x_coords_sorted = sorted(x_coords)
        gaps = []
        for i in range(1, len(x_coords_sorted)):
            gap = x_coords_sorted[i] - x_coords_sorted[i-1]
            if gap > 100:
                gaps.append(gap)

        if not gaps:
            return [rooms]

        max_gap = max(gaps)
        threshold = x_coords_sorted[x_coords_sorted.index(max_gap) - 1] + max_gap / 2

        plan1 = [room for room in rooms if room.get("x", 0) < threshold]
        plan2 = [room for room in rooms if room.get("x", 0) >= threshold]

        result = []
        if plan1:
            result.extend(self._detect_plan_boundaries(plan1))
        if plan2:
            result.extend(self._detect_plan_boundaries(plan2))

        return result

    def _validate_response_schema(self, data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Validate the response schema and apply corrections"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Ensure required top-level fields exist
        if "rooms" not in data:
            logger.warning("Missing 'rooms' field in response, adding empty array")
            data["rooms"] = []
        
        if not isinstance(data["rooms"], list):
            logger.error("'rooms' field is not a list, converting to empty array")
            data["rooms"] = []
        
        # Validate each room has required fields
        for i, room in enumerate(data["rooms"]):
            if not isinstance(room, dict):
                logger.warning(f"Room at index {i} is not a dict, skipping")
                continue
            
            # Ensure required room fields
            required_fields = ["name", "type", "x", "y", "width", "height", "area_px", "area_ft", "confidence"]
            for field in required_fields:
                if field not in room:
                    logger.debug(f"Room {i} missing field '{field}', applying default")
                    if field in ["x", "y", "width", "height", "area_px", "area_ft"]:
                        room[field] = 0
                    elif field == "confidence":
                        room[field] = 0.5
                    elif field == "type":
                        room[field] = "unknown"
                    elif field == "name":
                        room[field] = "Unknown"
        
        # Ensure total_area_px is calculated correctly
        if "total_area_px" not in data:
            total_area = sum(room.get("area_px", 0) for room in data["rooms"])
            data["total_area_px"] = total_area
            logger.info(f"Calculated total_area_px: {total_area}")
        
        return data

    def _parse_response(self, response_text: str, filename: str) -> Dict[str, Any]:
        """Parse the AI response into structured format with defensive parsing"""
        import logging
        import json
        import re
        from config import ALLOWED_ROOM_TYPES
        
        logger = logging.getLogger(__name__)
        
        logger.info(f"Parsing AI response for {filename}, response length: {len(response_text)}")
        
        response_text = response_text.strip()
        
        # Strip markdown wrappers
        if response_text.startswith("```json"):
            response_text = response_text[7:]
            logger.debug("Stripped ```json wrapper")
        if response_text.startswith("```"):
            response_text = response_text[3:]
            logger.debug("Stripped ``` wrapper")
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            logger.debug("Stripped closing ``` wrapper")
        response_text = response_text.strip()

        # Try to parse JSON directly first
        try:
            data = json.loads(response_text)
            logger.debug("Successfully parsed JSON directly")
        except json.JSONDecodeError as e:
            logger.warning(f"Direct JSON parse failed, attempting recovery: {str(e)}")
            # Attempt to recover malformed JSON
            # Try to extract JSON from text
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    logger.info("Successfully recovered JSON using regex extraction")
                except json.JSONDecodeError:
                    logger.warning("Regex extraction failed, attempting JSON fixes")
                    # Try to fix common JSON issues
                    fixed_json = response_text
                    # Fix trailing commas
                    fixed_json = re.sub(r',\s*}', '}', fixed_json)
                    fixed_json = re.sub(r',\s*]', ']', fixed_json)
                    # Fix unquoted keys
                    fixed_json = re.sub(r'(\w+):', r'"\1":', fixed_json)
                    try:
                        data = json.loads(fixed_json)
                        logger.info("Successfully recovered JSON after fixing common issues")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse AI response even after recovery attempts: {str(e)}")
                        return {
                            "error_code": "AI_PARSE_FAILED",
                            "error_message": f"Failed to parse AI response as JSON even after recovery attempts: {str(e)}",
                            "filename": filename,
                            "rooms": [],
                            "total_area_px": 0,
                            "drawing_type": "unknown",
                            "scale_detected": None,
                            "notes": f"Parse error: {str(e)}"
                        }
            else:
                logger.error("No valid JSON found in AI response")
                return {
                    "error_code": "AI_PARSE_FAILED",
                    "error_message": "No valid JSON found in AI response",
                    "filename": filename,
                    "rooms": [],
                    "total_area_px": 0,
                    "drawing_type": "unknown",
                    "scale_detected": None,
                    "notes": "No JSON found in response"
                }

            rooms = data.get("rooms", [])
            logger.info(f"Processing {len(rooms)} rooms from AI response")
            
            for room in rooms:
                room["x"] = room.get("x", 0)
                room["y"] = room.get("y", 0)
                room["width"] = room.get("width", 0)
                room["height"] = room.get("height", 0)
                room["area_px"] = room.get("area_px", 0)
                room["area_ft"] = room.get("area_ft", 0)
                
                # Clamp confidence values to 0-1 range
                confidence = room.get("confidence", 0.5)
                original_confidence = confidence
                room["confidence"] = max(0.0, min(1.0, confidence))
                if original_confidence != room["confidence"]:
                    logger.debug(f"Clamped confidence from {original_confidence} to {room['confidence']} for room {room.get('name', 'unknown')}")
                
                room["name"] = room.get("name", room.get("type", "Unknown"))[:50]

                # Validate and normalize room type
                room_type = room.get("type", "unknown").lower()
                if room_type not in ALLOWED_ROOM_TYPES:
                    logger.debug(f"Invalid room type '{room_type}' normalized to 'unknown'")
                    room["type"] = "unknown"
                else:
                    room["type"] = room_type

                label_area = self._parse_room_area_from_label(room["name"])
                if label_area:
                    logger.debug(f"Extracted area {label_area} sq ft from room label '{room['name']}'")
                    room["area_ft"] = label_area

            plan_clusters = self._detect_plan_boundaries(rooms)
            if len(plan_clusters) > 1:
                logger.info(f"Detected {len(plan_clusters)} separate floor plans")
                for i, cluster in enumerate(plan_clusters):
                    for room in cluster:
                        room["floor"] = i + 1

            total_area = sum(room.get("area_px", 0) for room in rooms)
            logger.info(f"Successfully parsed {len(rooms)} rooms with total area {total_area} px")

            # Validate schema and apply corrections
            validated_data = self._validate_response_schema({
                "rooms": rooms,
                "total_area_px": total_area,
                "drawing_type": data.get("drawing_type", "unknown"),
                "scale_detected": data.get("scale_detected"),
                "notes": data.get("notes", ""),
                "filename": filename,
                "provider": "multi_provider"
            }, filename)

            return validated_data

        except json.JSONDecodeError as e:
            return {
                "error_code": "AI_PARSE_FAILED",
                "error_message": f"Failed to parse AI response as JSON: {str(e)}",
                "filename": filename,
                "rooms": [],
                "total_area_px": 0,
                "drawing_type": "unknown",
                "scale_detected": None,
                "notes": f"Parse error: {str(e)}"
            }

    def _analyze_with_groq(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        """Analyze blueprint using Groq"""
        if not self.groq_client:
            return {
                "error_code": "GROQ_NOT_CONFIGURED",
                "error_message": "Groq client not initialized. Check GROQ_API_KEY.",
                "filename": filename,
                "rooms": [],
                "total_area_px": 0,
                "drawing_type": "unknown",
                "scale_detected": None,
                "notes": "Groq not available"
            }

        try:
            prompt = self._build_analysis_prompt()
            base64_image = self._encode_image(image_data)

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]

            model_name = "llama-3.2-90b-vision-preview"  # Use the working vision model

            response = self.groq_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=4096,
            )

            response_text = response.choices[0].message.content
            return self._parse_response(response_text, filename)

        except Exception as e:
            return {
                "error_code": "GROQ_API_ERROR",
                "error_message": str(e),
                "filename": filename,
                "rooms": [],
                "total_area_px": 0,
                "drawing_type": "unknown",
                "scale_detected": None,
                "notes": f"Groq error: {str(e)}"
            }

    def _analyze_with_gemini(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        """Analyze blueprint using Gemini"""
        if not self.gemini_model:
            return {
                "error_code": "GEMINI_NOT_CONFIGURED",
                "error_message": "Gemini model not initialized. Check GEMINI_API_KEY.",
                "filename": filename,
                "rooms": [],
                "total_area_px": 0,
                "drawing_type": "unknown",
                "scale_detected": None,
                "notes": "Gemini not available"
            }

        try:
            prompt = self._build_analysis_prompt()

            response = self.gemini_model.generate_content(
                [prompt, {"mime_type": "image/png", "data": image_data}],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4096,
                )
            )

            response_text = response.text
            return self._parse_response(response_text, filename)

        except Exception as e:
            return {
                "error_code": "GEMINI_API_ERROR",
                "error_message": str(e),
                "filename": filename,
                "rooms": [],
                "total_area_px": 0,
                "drawing_type": "unknown",
                "scale_detected": None,
                "notes": f"Gemini error: {str(e)}"
            }

    def analyze_blueprint(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Analyze blueprint using available providers with fallback and retry logic

        Args:
            image_data: Binary image data
            filename: Name of the file being analyzed

        Returns:
            Parsed analysis result with rooms and metadata or error code
        """
        last_error = None

        for provider in AI_PROVIDERS:
            if provider == "openai":
                result = self._analyze_with_openai(image_data, filename)
                # Retry once on empty response
                if result.get("error_code") == "AI_EMPTY_RESPONSE":
                    result = self._analyze_with_openai(image_data, filename)
                if "error_code" not in result or result["error_code"] not in ["OPENAI_NOT_CONFIGURED", "OPENAI_API_ERROR"]:
                    result["provider_used"] = "openai"
                    return result
                last_error = result.get("error_message", last_error)

            elif provider == "groq":
                result = self._analyze_with_groq(image_data, filename)
                # Retry once on empty response
                if result.get("error_code") == "AI_EMPTY_RESPONSE":
                    result = self._analyze_with_groq(image_data, filename)
                if "error_code" not in result or result["error_code"] not in ["GROQ_NOT_CONFIGURED", "GROQ_API_ERROR"]:
                    result["provider_used"] = "groq"
                    return result
                last_error = result.get("error_message", last_error)

            elif provider == "gemini":
                result = self._analyze_with_gemini(image_data, filename)
                # Retry once on empty response
                if result.get("error_code") == "AI_EMPTY_RESPONSE":
                    result = self._analyze_with_gemini(image_data, filename)
                if "error_code" not in result or result["error_code"] not in ["GEMINI_NOT_CONFIGURED", "GEMINI_API_ERROR"]:
                    result["provider_used"] = "gemini"
                    return result
                last_error = result.get("error_message", last_error)

        # All providers failed
        return {
            "error_code": "ALL_PROVIDERS_FAILED",
            "error_message": f"All AI providers failed. Last error: {last_error}",
            "filename": filename,
            "rooms": [],
            "total_area_px": 0,
            "drawing_type": "unknown",
            "scale_detected": None,
            "notes": "No AI provider available or all providers failed"
        }
