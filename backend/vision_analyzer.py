import json
import logging
import os
from io import BytesIO

from google import genai
from google.genai import types
from PIL import Image

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

MODEL = "gemini-2.0-flash"

# =====================================================
# CLIENT
# =====================================================


def get_client():
    return genai.Client(api_key=GOOGLE_API_KEY)


# =====================================================
# PROMPT
# =====================================================

PROMPT = """
Analyze this architectural blueprint.

Return ONLY valid JSON.

DO NOT hallucinate rooms.
DO NOT estimate dimensions.
ONLY return rooms clearly visible.
If uncertain return null.

Required JSON structure:

{
  "rooms": [
    {
      "name": "ROOM NAME",
      "area_sqft": 120,
      "width_ft": 10,
      "height_ft": 12
    }
  ],
  "total_area_sqft": 1200,
  "features": ["STAIR", "BALCONY"]
}
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
        print(f"VISION RESPONSE: {raw[:200]}...") # Log first bit for debug
        data = json.loads(raw)
        return data
    except Exception as e:
        print(f"VISION ERROR: {str(e)}")
        return {}


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
            "confidence": 0.85,
            "source": "vision_ai",
        })

    legacy_rooms = legacy_data.get("room_data", [])
    
    if not legacy_rooms:
        legacy_data["room_data"] = vision_rooms
        legacy_data["method_used"] = legacy_data.get("method_used", "") + " (Vision AI Primary)"
    else:
        # If we have OCR rooms, only add AI rooms that aren't already found
        existing_names = {r["room"].upper() for r in legacy_rooms}
        for vr in vision_rooms:
            if vr["room"].upper() not in existing_names:
                legacy_rooms.append(vr)
        legacy_data["room_data"] = legacy_rooms

    # Recalculate total area from all rooms
    total_area = sum(float(r.get("area") or 0) for r in legacy_data["room_data"])
    legacy_data["total_area"] = round(total_area, 2)
    legacy_data["vision_used"] = True
    
    return legacy_data


# =====================================================
# PUBLIC FUNCTIONS
# =====================================================


def analyze_pdf_with_vision(file_bytes, legacy_result):
    try:
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(
            file_bytes,
            dpi=150,
            first_page=1,
            last_page=1,
        )

        if not images:
            return legacy_result

        image_bytes = pil_to_bytes(images[0])

        vision_data = call_gemini(image_bytes)

        return merge_results(vision_data, legacy_result)

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