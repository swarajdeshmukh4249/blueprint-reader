import json
import logging
import os
from io import BytesIO

from google import genai
from google.genai import types
from PIL import Image

logger = logging.getLogger(__name__)

# Manual .env loading fallback
if not os.environ.get("GOOGLE_API_KEY") and os.path.exists(".env"):
    try:
        with open(".env", "r") as f:
            for line in f:
                if "GOOGLE_API_KEY=" in line:
                    os.environ["GOOGLE_API_KEY"] = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

MODEL = "gemini-1.5-flash"

# =====================================================
# CLIENT
# =====================================================


def get_client():
    return genai.Client(api_key=GOOGLE_API_KEY)


# =====================================================
# PROMPT
# =====================================================

PROMPT = """
Analyze this architectural blueprint carefully.
Your task is to extract every room, its name, and its area (sq ft).

Look for labels like "BEDROOM 120 SQ FT" or "KITCHEN 10' x 12'".
If you see dimensions (like 10' x 12'), multiply them to get the square footage.

Return a valid JSON object:
{
  "rooms": [
    {"name": "Master Bedroom", "area_sqft": 144, "width_ft": 12, "height_ft": 12},
    ...
  ],
  "total_area_sqft": 1250,
  "features": ["Balcony", "Kitchen Sink"]
}

Be thorough. Even if a room area is small, include it.
"""


# =====================================================
# IMAGE HELPERS
# =====================================================


def pil_to_bytes(img):
    img = img.convert("RGB")

    buf = BytesIO()

    img.save(buf, format="JPEG", quality=90)

    return buf.getvalue()


# =====================================================
# GEMINI CALL
# =====================================================


def call_gemini(image_bytes):
    client = get_client()
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                ),
                PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        raw = response.text.strip()
        return json.loads(raw)
    except Exception as e:
        print(f"VISION ERROR: {str(e)}")
        # Return the error so it shows up in legacy_data
        return {"error": str(e), "rooms": []}


# =====================================================
# SAFE MERGE
# =====================================================


def merge_results(vision_data, legacy_data):
    if not vision_data or not vision_data.get("rooms"):
        return legacy_data

    vision_rooms = []
    for room in vision_data.get("rooms", []):
        area = room.get("area_sqft") or 0
        if not area and room.get("width_ft") and room.get("height_ft"):
            area = room["width_ft"] * room["height_ft"]
        
        vision_rooms.append({
            "room": room.get("name") or "Unnamed Room",
            "area": round(float(area), 2) if area else 0,
            "width": room.get("width_ft"),
            "height": room.get("height_ft"),
            "confidence": 0.95,
            "source": "vision_ai",
        })

    # If AI found rooms, FORCE use them. We trust the AI more than OCR/Text patterns.
    if vision_rooms:
        legacy_data["room_data"] = vision_rooms
        legacy_data["method_used"] = "AI Vision Analysis"
        legacy_data["vision_used"] = True
    
    total_area = sum(float(r.get("area") or 0) for r in legacy_data.get("room_data", []))
    legacy_data["total_area"] = round(total_area, 2)
    
    return legacy_data


# =====================================================
# PUBLIC FUNCTIONS
# =====================================================


def analyze_pdf_with_vision(file_bytes, legacy_result):
    try:
        from pdf2image import convert_from_bytes

        import time
        images = convert_from_bytes(
            file_bytes,
            dpi=300,
            first_page=1,
            last_page=2, # Reduced to 2 pages to save your API quota
        )

        if not images:
            return legacy_result

        for img in images:
            image_bytes = pil_to_bytes(img)
            vision_data = call_gemini(image_bytes)
            
            if vision_data and vision_data.get("rooms"):
                return merge_results(vision_data, legacy_result)
            
            # Wait 2 seconds before checking next page to avoid 429 limit
            time.sleep(2)
        
        return legacy_result

    except Exception as e:
        logger.error(e)
        return legacy_result



def analyze_image_with_vision(file_bytes, legacy_result):
    try:
        image = Image.open(BytesIO(file_bytes))

        image_bytes = pil_to_bytes(image)

        vision_data = call_gemini(image_bytes)

        return merge_results(vision_data, legacy_result)

    except Exception as e:
        logger.error(e)
        return legacy_result



def analyze_dxf_with_vision(file_bytes, legacy_result):
    try:
        return legacy_result

    except Exception as e:
        logger.error(e)
        return legacy_result