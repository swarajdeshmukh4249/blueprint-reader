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
- total_area_sqft: use NET TOTAL / TOTAL BUILT UP from AREA STATEMENT table if visible (sq ft column), else sum of room areas, else null.
- area_statement_net_sqft: official net FSI+built-up total from AREA STATEMENT (sq ft), if shown.
- features: optional list from STAIR, BALCONY, PARKING, LIFT, TERRACE, CORRIDOR.

{
  "rooms": [
    {"name": "BEDROOM", "area_sqft": 120, "width_ft": null, "height_ft": null}
  ],
  "total_area_sqft": null,
  "area_statement_net_sqft": null,
  "features": []
}
"""


def merge_vision_pages(vision_pages: list[dict]) -> dict:
    """Combine room lists from multiple plan pages."""
    rooms: list[dict] = []
    features: list[str] = []
    total = None
    stmt_net = None

    for data in vision_pages:
        if not data:
            continue
        for room in data.get("rooms") or []:
            if room and room.get("name"):
                rooms.append(room)
        for f in data.get("features") or []:
            if f and str(f).upper() not in features:
                features.append(str(f).upper())
        if data.get("area_statement_net_sqft"):
            stmt_net = data["area_statement_net_sqft"]
        elif data.get("total_area_sqft") and not total:
            total = data["total_area_sqft"]

    out: dict = {"rooms": rooms, "features": features}
    if stmt_net:
        out["area_statement_net_sqft"] = stmt_net
        out["total_area_sqft"] = stmt_net
    elif total:
        out["total_area_sqft"] = total
    return out


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
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set — Vision analysis skipped")
        return {}

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
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        logger.error("Vision API error: %s", e)
        return {"error": str(e), "rooms": []}


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
    if vision_data.get("error"):
        legacy_data["notes"] = (
            (legacy_data.get("notes") or "") + f" AI Error: {vision_data['error']}"
        ).strip()

    if not vision_data or not vision_data.get("rooms"):
        return legacy_data

    legacy_rooms = list(legacy_data.get("room_data") or [])

    vision_rooms = []
    for room in vision_data.get("rooms", []):
        name = _norm_room(room.get("name") or "")
        if not name:
            continue
        area = room.get("area_sqft") or 0
        if not area and room.get("width_ft") and room.get("height_ft"):
            area = float(room["width_ft"]) * float(room["height_ft"])
        vision_rooms.append({
            "room": name,
            "label": name,
            "area": round(float(area), 2) if area else None,
            "width": room.get("width_ft"),
            "height": room.get("height_ft"),
            "unit": "sq ft",
            "floor": None,
            "wall_type": None,
            "confidence": 0.85,
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

    stmt_net = vision_data.get("area_statement_net_sqft")
    vision_total = stmt_net or vision_data.get("total_area_sqft")
    legacy_sum = sum(float(r.get("area") or 0) for r in final_rooms)
    if vision_total and (legacy_sum <= 0 or float(vision_total) > legacy_sum * 1.05):
        legacy_data["total_area"] = float(vision_total)
    else:
        legacy_data["total_area"] = legacy_sum
    if stmt_net:
        legacy_data.setdefault("area_statement", {})["net_built_up_sqft"] = float(stmt_net)

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


def analyze_pdf_with_vision(file_bytes, legacy_result, max_pages: int = 4):
    try:
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(
            file_bytes,
            dpi=175,
            first_page=1,
            last_page=max_pages,
        )

        if not images:
            return legacy_result

        import time

        page_results = []
        for i, img in enumerate(images[:max_pages]):
            page_results.append(call_gemini(pil_to_bytes(img)))
            if i < len(images[:max_pages]) - 1:
                time.sleep(2)  # reduce Gemini 429 rate limits

        vision_data = merge_vision_pages(page_results)
        if not vision_data.get("rooms"):
            return legacy_result

        merged = merge_results(vision_data, legacy_result)
        merged["vision_pages_analyzed"] = len(page_results)
        return merged

    except Exception as e:
        logger.error("PDF vision failed: %s", e)
        return legacy_result



def _resize_for_api(img: Image.Image, max_dim: int = 4096) -> Image.Image:
    w, h = img.size
    if max(w, h) <= max_dim:
        return img
    scale = max_dim / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)


def analyze_image_with_vision(file_bytes, legacy_result):
    try:
        image = _resize_for_api(Image.open(BytesIO(file_bytes)).convert("RGB"))
        vision_data = call_gemini(pil_to_bytes(image))
        if not vision_data:
            return legacy_result
        return merge_results(vision_data, legacy_result)

    except Exception as e:
        logger.error("Image vision failed: %s", e)
        return legacy_result



def analyze_dxf_with_vision(file_bytes, legacy_result):
    try:
        return legacy_result

    except Exception as e:
        logger.error(e)
        return legacy_result