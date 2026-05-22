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

    try:
        return json.loads(raw)
    except Exception:
        return {}


# =====================================================
# SAFE MERGE
# =====================================================


def merge_results(vision_data, legacy_data):
    if not vision_data:
        return legacy_data

    legacy_rooms = legacy_data.get("room_data", [])

    vision_rooms = []

    for room in vision_data.get("rooms", []):
        vision_rooms.append({
            "room": room.get("name"),
            "area": room.get("area_sqft"),
            "width": room.get("width_ft"),
            "height": room.get("height_ft"),
            "confidence": 0.70,
            "source": "vision_ai",
        })

    # IMPORTANT
    # NEVER overwrite deterministic extraction

    if legacy_rooms:

        for legacy_room in legacy_rooms:

            for vision_room in vision_rooms:

                if legacy_room["room"] == vision_room["room"]:

                    if not legacy_room.get("area"):
                        legacy_room["area"] = vision_room.get("area")

                    if not legacy_room.get("width"):
                        legacy_room["width"] = vision_room.get("width")

                    if not legacy_room.get("height"):
                        legacy_room["height"] = vision_room.get("height")

        final_rooms = legacy_rooms

    else:
        final_rooms = vision_rooms

    total_area = sum(
        r.get("area", 0)
        for r in final_rooms
        if r.get("confidence", 0) >= 0.7
    )

    legacy_data["room_data"] = final_rooms
    legacy_data["total_area"] = total_area
    legacy_data["vision_used"] = True
    legacy_data["vision_model"] = MODEL

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