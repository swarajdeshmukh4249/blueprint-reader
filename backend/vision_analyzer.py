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
Analyze this architectural floor plan image.

Return ONLY valid JSON (no markdown).

Rules:
- List ONLY rooms you can clearly read from labels or dimension text on the drawing.
- For each room include area_sqft if written on the plan; otherwise omit area_sqft (do not guess).
- Use standard names: MASTER BEDROOM, BEDROOM, LIVING ROOM, KITCHEN, BATHROOM, TOILET, BALCONY, etc.
- total_area_sqft: sum of labeled room areas if shown, else null.
- features: optional list from STAIR, BALCONY, PARKING, LIFT, TERRACE, CORRIDOR.

{
  "rooms": [
    {"name": "BEDROOM", "area_sqft": 120, "width_ft": null, "height_ft": null}
  ],
  "total_area_sqft": null,
  "features": []
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


def _norm_room(name: str) -> str:
    if not name:
        return ""
    n = str(name).upper().strip()
    aliases = {
        "BED RM": "BEDROOM", "BED ROOM": "BEDROOM",
        "LIVING": "LIVING ROOM", "DINING": "DINING ROOM",
    }
    return aliases.get(n, n)


def merge_results(vision_data, legacy_data):
    if not vision_data:
        return legacy_data

    legacy_rooms = list(legacy_data.get("room_data") or [])

    vision_rooms = []
    for room in vision_data.get("rooms", []):
        name = _norm_room(room.get("name") or "")
        if not name:
            continue
        vision_rooms.append({
            "room": name,
            "label": name,
            "area": room.get("area_sqft"),
            "width": room.get("width_ft"),
            "height": room.get("height_ft"),
            "unit": "sq ft",
            "floor": None,
            "wall_type": None,
            "confidence": 0.72,
            "source": "vision_ai",
        })

    if legacy_rooms:
        for legacy_room in legacy_rooms:
            lr = _norm_room(legacy_room.get("room", ""))
            legacy_room["room"] = lr
            for vision_room in vision_rooms:
                if lr == vision_room["room"]:
                    if not legacy_room.get("area") and vision_room.get("area"):
                        legacy_room["area"] = vision_room["area"]
                        legacy_room["confidence"] = max(
                            legacy_room.get("confidence", 0), 0.78,
                        )
                    if not legacy_room.get("width"):
                        legacy_room["width"] = vision_room.get("width")
                    if not legacy_room.get("height"):
                        legacy_room["height"] = vision_room.get("height")
        matched = {_norm_room(r.get("room", "")) for r in legacy_rooms}
        for vr in vision_rooms:
            if _norm_room(vr["room"]) not in matched and vr.get("area"):
                legacy_rooms.append(vr)
        final_rooms = legacy_rooms
    else:
        final_rooms = vision_rooms

    vision_total = vision_data.get("total_area_sqft")
    legacy_sum = sum(float(r.get("area") or 0) for r in final_rooms)
    if vision_total and (legacy_sum <= 0 or vision_total > legacy_sum * 1.1):
        legacy_data["total_area"] = float(vision_total)
    else:
        legacy_data["total_area"] = legacy_sum

    features = list(legacy_data.get("features_found") or [])
    for f in vision_data.get("features") or []:
        if f and str(f).upper() not in features:
            features.append(str(f).upper())
    legacy_data["features_found"] = features

    legacy_data["room_data"] = final_rooms
    legacy_data["vision_used"] = True
    legacy_data["vision_model"] = MODEL
    legacy_data["vision_confidence"] = 0.72 if final_rooms else 0.0

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