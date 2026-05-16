"""
vision_analyzer.py
------------------
Gemini 2.0 Flash Vision integration for AI Blueprint Reader.

Handles all file types:
  - PDF   → sent directly to Gemini (native PDF support, no conversion needed)
  - Image → sent directly to Gemini
  - DXF   → rendered to image via ezdxf matplotlib backend → sent to Gemini
  - DWG   → same render path as DXF

Free tier: 1,500 requests/day — plenty for dev + early users.
Get your key at: https://aistudio.google.com
"""

import json
import logging
import os
import tempfile
from io import BytesIO
from typing import Any

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

GEMINI_MODEL      = "gemini-2.0-flash"
MAX_IMAGE_SIDE    = 2000
MAX_PAGES_TO_SEND = 3

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


# ─────────────────────────────────────────────
# Client setup
# ─────────────────────────────────────────────

def _get_client():
    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY is not set. "
            "Get a free key at https://aistudio.google.com and add it to backend/.env"
        )
    return genai.Client(api_key=GOOGLE_API_KEY)


# ─────────────────────────────────────────────
# Prompt
# ─────────────────────────────────────────────

USER_PROMPT = """Analyze this architectural blueprint carefully.

Return ONLY a JSON object with this exact structure:

{
  "drawing_type": "floor_plan" | "site_plan" | "elevation" | "section" | "unknown",
  "unit_system": "feet" | "meters" | "mm" | "unknown",
  "floor_count": <integer, number of floor levels visible or inferable>,
  "confidence": <float 0.0-1.0, your overall confidence in the extraction>,
  "rooms": [
    {
      "name": "<room name exactly as labeled, e.g. MASTER BEDROOM, KITCHEN>",
      "instance_label": "<full label with number if present, e.g. BEDROOM 1>",
      "width_ft": <float or null>,
      "height_ft": <float or null>,
      "area_sqft": <float or null>,
      "wall_type": "external" | "internal" | "partition" | "unknown",
      "floor": "<floor name e.g. GROUND FLOOR, or null>"
    }
  ],
  "features": ["<feature name, e.g. STAIR, BALCONY, PARKING>"],
  "openings": {
    "doors": [{"room": "<room name>", "count": <int>, "type": "<main/toilet/bedroom/etc>"}],
    "windows": [{"room": "<room name>", "count": <int>}]
  },
  "total_area_sqft": <float or null>,
  "site_area_sqft": <float or null>,
  "notes": "<anything unusual or ambiguous, or null>"
}

Rules:
- Convert all dimension labels (e.g. 12'-0\", 3600mm) to feet for width_ft/height_ft.
- If only area is labeled (e.g. 120 SQ FT), set area_sqft directly.
- For rooms with no measurable data, set those fields to null — do NOT guess.
- Features include: GROUND FLOOR, FIRST FLOOR, TERRACE, STAIR, BALCONY, PARKING, CAR PORCH, LIFT, CORRIDOR.
- Return ONLY the JSON object."""


# ─────────────────────────────────────────────
# Image helpers
# ─────────────────────────────────────────────

def _resize_pil(img):
    w, h = img.size
    if max(w, h) > MAX_IMAGE_SIDE:
        scale = MAX_IMAGE_SIDE / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    return img


def _pil_to_bytes(img) -> bytes:
    img = _resize_pil(img.convert("RGB"))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _dxf_to_pil(file_bytes: bytes):
    """Render DXF to PIL image via ezdxf matplotlib backend. Returns None on failure."""
    try:
        import ezdxf
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from PIL import Image as PILImage

        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            doc = ezdxf.readfile(tmp_path)
            msp = doc.modelspace()
            fig = plt.figure(figsize=(16, 12), dpi=150)
            ax = fig.add_axes([0, 0, 1, 1])
            ctx = RenderContext(doc)
            backend = MatplotlibBackend(ax)
            Frontend(ctx, backend).draw_layout(msp)
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white", dpi=150)
            plt.close(fig)
            buf.seek(0)
            return PILImage.open(buf).copy()
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.warning(f"DXF render failed: {e}")
        return None


# ─────────────────────────────────────────────
# Gemini API call
# ─────────────────────────────────────────────

def _call_gemini(parts: list) -> dict[str, Any]:
    client = _get_client()
    contents = []
    for part in parts:
        if isinstance(part, dict) and "mime_type" in part:
            contents.append(types.Part.from_bytes(
                data=part["data"],
                mime_type=part["mime_type"],
            ))
        else:
            contents.append(part)
    contents.append(USER_PROMPT)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
            system_instruction=(
                "You are a senior architect and quantity surveyor with 20+ years of experience "
                "reading architectural blueprints, CAD drawings, and construction documents. "
                "You extract precise structured data for Bill of Quantities (BOQ) generation. "
                "Always respond with valid JSON only — no markdown, no preamble, no explanation outside the JSON."
            ),
        ),
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned non-JSON: {e}\nRaw: {raw[:500]}")
        return {}


# ─────────────────────────────────────────────
# Quota / error helper
# ─────────────────────────────────────────────

def _is_quota_error(e: Exception) -> bool:
    msg = str(e)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()


# ─────────────────────────────────────────────
# Merge Gemini output with legacy parser data
# ─────────────────────────────────────────────

def _merge_with_legacy(gemini_data: dict, legacy_data: dict) -> dict:
    merged = dict(legacy_data)

    if not gemini_data:
        merged["vision_used"] = False
        merged["vision_error"] = "Gemini returned no structured data"
        return merged

    rooms      = gemini_data.get("rooms", [])
    features   = gemini_data.get("features", [])
    openings   = gemini_data.get("openings", {"doors": [], "windows": []})
    total_area = gemini_data.get("total_area_sqft") or 0.0

    room_data = []
    for r in rooms:
        room_data.append({
            "room":       r.get("instance_label") or r.get("name", "Unknown"),
            "width":      r.get("width_ft"),
            "height":     r.get("height_ft"),
            "area":       r.get("area_sqft") or 0.0,
            "unit":       "sq ft",
            "source":     "Gemini Vision",
            "floor":      r.get("floor"),
            "wall_type":  r.get("wall_type", "unknown"),
            "confidence": gemini_data.get("confidence", 1.0),
        })

    if not total_area and room_data:
        rooms_with_area = [r for r in room_data if r.get("area") and r["area"] > 0]
        if rooms_with_area:
            total_area = round(sum(r["area"] for r in rooms_with_area), 2)
            missing = len(room_data) - len(rooms_with_area)
            if missing > 0:
                existing_notes = gemini_data.get("notes") or ""
                gemini_data["notes"] = (
                    existing_notes +
                    f" [Note: {missing} room(s) had no extractable dimensions — total area may be understated.]"
                ).strip()

    room_types     = list({r.get("name", "") for r in rooms if r.get("name")})
    room_instances = [r.get("instance_label") or r.get("name", "") for r in rooms]

    merged.update({
        "vision_used":          True,
        "vision_model":         GEMINI_MODEL,
        "vision_confidence":    gemini_data.get("confidence", 1.0),
        "drawing_type":         gemini_data.get("drawing_type", "unknown"),
        "unit_system":          gemini_data.get("unit_system", "unknown"),
        "floor_count":          gemini_data.get("floor_count", 1),
        "rooms_found":          room_types,
        "room_instances_found": room_instances,
        "room_counts":          {rt: room_instances.count(rt) for rt in room_types},
        "room_count":           len(room_instances),
        "features_found":       features,
        "room_data":            room_data,
        "total_area":           total_area,
        "openings":             openings,
        "site_area_sqft":       gemini_data.get("site_area_sqft"),
        "vision_notes":         gemini_data.get("notes"),
    })

    if total_area > 0:
        from blueprint_logic import estimate_materials, estimate_costs
        merged["materials"] = estimate_materials(total_area)
        merged["costs"]     = estimate_costs(total_area)

    return merged


# ─────────────────────────────────────────────
# Public entry points
# ─────────────────────────────────────────────

def analyze_pdf_with_vision(file_bytes: bytes, legacy_result: dict) -> dict:
    try:
        pdf_part = {"mime_type": "application/pdf", "data": file_bytes}
        gemini_data = _call_gemini([pdf_part])
        return _merge_with_legacy(gemini_data, legacy_result)
    except Exception as e:
        if _is_quota_error(e):
            logger.warning("Gemini quota exhausted — returning legacy result for PDF")
            legacy_result["vision_used"] = False
            legacy_result["vision_error"] = "Gemini quota exhausted"
        else:
            logger.error(f"Vision PDF analysis failed: {e}")
            legacy_result["vision_used"] = False
            legacy_result["vision_error"] = str(e)
        return legacy_result


def analyze_image_with_vision(file_bytes: bytes, legacy_result: dict) -> dict:
    try:
        from PIL import Image as PILImage
        img = PILImage.open(BytesIO(file_bytes))
        img_part = {"mime_type": "image/jpeg", "data": _pil_to_bytes(img)}
        gemini_data = _call_gemini([img_part])
        return _merge_with_legacy(gemini_data, legacy_result)
    except Exception as e:
        if _is_quota_error(e):
            logger.warning("Gemini quota exhausted — returning legacy result for image")
            legacy_result["vision_used"] = False
            legacy_result["vision_error"] = "Gemini quota exhausted"
        else:
            logger.error(f"Vision image analysis failed: {e}")
            legacy_result["vision_used"] = False
            legacy_result["vision_error"] = str(e)
        return legacy_result


def analyze_dxf_with_vision(file_bytes: bytes, legacy_result: dict) -> dict:
    try:
        img = _dxf_to_pil(file_bytes)
        if img is None:
            raise ValueError("DXF render produced no image")
        img_part = {"mime_type": "image/jpeg", "data": _pil_to_bytes(img)}
        gemini_data = _call_gemini([img_part])
        return _merge_with_legacy(gemini_data, legacy_result)
    except Exception as e:
        if _is_quota_error(e):
            logger.warning("Gemini quota exhausted — returning legacy result for DXF")
            legacy_result["vision_used"] = False
            legacy_result["vision_error"] = "Gemini quota exhausted"
        else:
            logger.error(f"Vision DXF analysis failed: {e}")
            legacy_result["vision_used"] = False
            legacy_result["vision_error"] = str(e)
        return legacy_result


def analyze_dwg_with_vision(file_bytes: bytes, legacy_result: dict) -> dict:
    try:
        img = _dxf_to_pil(file_bytes)
        if img is None:
            raise ValueError(
                "DWG could not be rendered. Convert to DXF using AutoCAD, LibreCAD, "
                "or the free ODA File Converter (opendesign.com/guestfiles/oda_file_converter)."
            )
        img_part = {"mime_type": "image/jpeg", "data": _pil_to_bytes(img)}
        gemini_data = _call_gemini([img_part])
        result = _merge_with_legacy(gemini_data, legacy_result)
        result["source_type"] = "dwg"
        return result
    except Exception as e:
        if _is_quota_error(e):
            logger.warning("Gemini quota exhausted — returning legacy result for DWG")
            legacy_result["vision_used"] = False
            legacy_result["vision_error"] = "Gemini quota exhausted"
        else:
            logger.error(f"Vision DWG analysis failed: {e}")
            legacy_result["vision_used"] = False
            legacy_result["vision_error"] = str(e)
            legacy_result["note"] = "DWG could not be parsed. Convert to DXF for best results."
        return legacy_result