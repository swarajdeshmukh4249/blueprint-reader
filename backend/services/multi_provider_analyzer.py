"""
Multi-Provider Vision Analyzer
Supports multiple AI providers with automatic fallback
"""
import base64
import re
from typing import Dict, Any, List, Optional
from config import (
    GROQ_API_KEY, GEMINI_API_KEY,
    GROQ_MODEL_FAST, GEMINI_MODEL_FAST,
    GROQ_MAX_RETRIES, GEMINI_MAX_RETRIES,
    AI_PROVIDERS
)

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
        self.groq_client = None
        self.gemini_model = None

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
                model_name = GEMINI_MODEL_FAST if use_fast_model else "gemini-1.5-pro"
                self.gemini_model = genai.GenerativeModel(model_name)
            except Exception as e:
                print(f"Failed to initialize Gemini model: {e}")

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

    def _parse_response(self, response_text: str, filename: str) -> Dict[str, Any]:
        """Parse the AI response into structured format"""
        try:
            import json
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            data = json.loads(response_text)

            rooms = data.get("rooms", [])
            for room in rooms:
                room["x"] = room.get("x", 0)
                room["y"] = room.get("y", 0)
                room["width"] = room.get("width", 0)
                room["height"] = room.get("height", 0)
                room["area_px"] = room.get("area_px", 0)
                room["area_ft"] = room.get("area_ft", 0)
                room["confidence"] = room.get("confidence", 0.5)
                room["name"] = room.get("name", room.get("type", "Unknown"))[:50]

                label_area = self._parse_room_area_from_label(room["name"])
                if label_area:
                    room["area_ft"] = label_area

            plan_clusters = self._detect_plan_boundaries(rooms)
            if len(plan_clusters) > 1:
                for i, cluster in enumerate(plan_clusters):
                    for room in cluster:
                        room["floor"] = i + 1

            total_area = sum(room.get("area_px", 0) for room in rooms)

            return {
                "rooms": rooms,
                "total_area_px": total_area,
                "drawing_type": data.get("drawing_type", "unknown"),
                "scale_detected": data.get("scale_detected"),
                "notes": data.get("notes", ""),
                "filename": filename,
                "provider": "multi_provider"
            }

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

            model_name = GROQ_MODEL_FAST if self.use_fast_model else "llama-3.2-90b-vision-preview"

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
        Analyze blueprint using available providers with fallback

        Args:
            image_data: Binary image data
            filename: Name of the file being analyzed

        Returns:
            Parsed analysis result with rooms and metadata or error code
        """
        last_error = None

        for provider in AI_PROVIDERS:
            if provider == "groq":
                result = self._analyze_with_groq(image_data, filename)
                if "error_code" not in result or result["error_code"] not in ["GROQ_NOT_CONFIGURED", "GROQ_API_ERROR"]:
                    result["provider_used"] = "groq"
                    return result
                last_error = result.get("error_message", last_error)

            elif provider == "gemini":
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
