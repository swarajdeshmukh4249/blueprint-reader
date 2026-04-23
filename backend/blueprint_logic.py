import os
import re
import tempfile
from io import BytesIO
from typing import Any, Optional

import cv2
import ezdxf
import numpy as np
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from pypdf import PdfReader
from shapely.geometry import Polygon

print("NEW BLUEPRINT LOGIC RUNNING")

# Vision LLM — imported lazily so legacy mode still works if google-generativeai not installed
try:
    from vision_analyzer import (
        analyze_pdf_with_vision,
        analyze_image_with_vision,
        analyze_dxf_with_vision,
        analyze_dwg_with_vision,
    )
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

# Set to False to disable Vision and use legacy OCR/regex only
VISION_ENABLED = os.environ.get("VISION_ENABLED", "true").lower() == "true"
ROOM_KEYWORDS = [
    "MASTER BEDROOM",
    "BED ROOM",
    "BEDROOM",
    "BEDRM",
    "LIVING ROOM",
    "LIVING",
    "SITTING ROOM",
    "DINING ROOM",
    "DINING",
    "KITCHEN",
    "TOILET",
    "BATHROOM",
    "BATH",
    "WC",
    "W.C.",
    "LOBBY",
    "PASSAGE",
    "HALL",
    "HALLWAY",
    "ENTRY",
    "FOYER",
    "STAIR",
    "TERRACE",
    "BALCONY",
    "CAR PARK",
    "CAR PORCH",
    "PARKING",
    "STORE",
    "STORAGE",
    "UTILITY",
    "UTILITIES",
    "WASH",
    "VERANDA",
    "CLOSET",
    "WALK IN CLOSET",
    "WALK-IN CLOSET",
    "PANTRY",
    "LAUNDRY",
]

FEATURE_KEYWORDS = [
    "GROUND FLOOR",
    "FIRST FLOOR",
    "SECOND FLOOR",
    "TERRACE",
    "STAIR",
    "BALCONY",
    "PARKING",
    "CAR PORCH",
    "PORCH",
    "ROAD",
]

OPENING_KEYWORDS = [
    "MAIN DOOR",
    "DOOR",
    "TOILET DOOR",
    "WINDOW",
    "VENTILATOR",
]

ROOM_KEYWORDS_SORTED = sorted(ROOM_KEYWORDS, key=len, reverse=True)
FEATURE_KEYWORDS_SORTED = sorted(FEATURE_KEYWORDS, key=len, reverse=True)
OPENING_KEYWORDS_SORTED = sorted(OPENING_KEYWORDS, key=len, reverse=True)

ROOM_ALIAS_PATTERNS: list[tuple[str, str]] = [
    ("MASTER BEDROOM", r"MASTER\s+BED(?:\s*ROOM)?"),
    ("BEDROOM", r"BED(?:\s*ROOM|RM)?"),
    ("LIVING ROOM", r"LIVING(?:\s+ROOM)?"),
    ("SITTING ROOM", r"SITTING\s+ROOM"),
    ("DINING ROOM", r"DINING(?:\s+ROOM)?"),
    ("KITCHEN", r"KITCHEN"),
    ("BATHROOM", r"BATH(?:ROOM)?"),
    ("TOILET", r"TOILET"),
    ("WC", r"W\.?\s*C\.?"),
    ("LOBBY", r"LOBBY"),
    ("PASSAGE", r"PASSAGE"),
    ("HALLWAY", r"HALL(?:WAY)?"),
    ("ENTRY", r"ENTRY"),
    ("FOYER", r"FOYER"),
    ("STAIR", r"STAIR(?:CASE)?"),
    ("TERRACE", r"TERRACE"),
    ("BALCONY", r"BALCONY"),
    ("CAR PARK", r"CAR\s+PARK"),
    ("CAR PORCH", r"CAR\s+PORCH"),
    ("PARKING", r"PARKING"),
    ("STORE", r"STORE"),
    ("STORAGE", r"STORAGE"),
    ("UTILITY", r"UTILIT(?:Y|IES)"),
    ("WASH", r"WASH"),
    ("VERANDA", r"VERANDA"),
    ("CLOSET", r"(?:WALK[-\s]?IN\s+)?CLOSET"),
    ("PANTRY", r"PANTRY"),
    ("LAUNDRY", r"LAUNDRY"),
]

AREA_UNIT_PATTERNS = [
    r"SQ\s*\.?\s*FT",
    r"SQFT",
    r"SFT",
    r"SF",
    r"FT2",
    r"FT\^2",
    r"SQ\s*FEET",
]

ROOM_INSTANCE_PATTERNS: list[tuple[str, str]] = [
    ("MASTER BEDROOM", r"MASTER\s+BED(?:\s*ROOM)?\s*\d*"),
    ("BEDROOM", r"BED(?:\s*ROOM|RM)?\s*\d*"),
    ("LIVING ROOM", r"LIVING(?:\s+ROOM)?\s*\d*"),
    ("SITTING ROOM", r"SITTING\s+ROOM\s*\d*"),
    ("DINING ROOM", r"DINING(?:\s+ROOM)?\s*\d*"),
    ("KITCHEN", r"KITCHEN\s*\d*"),
    ("BATHROOM", r"BATH(?:ROOM)?\s*\d*"),
    ("TOILET", r"TOILET\s*\d*"),
    ("WC", r"W\.?\s*C\.?\s*\d*"),
    ("LOBBY", r"LOBBY\s*\d*"),
    ("PASSAGE", r"PASSAGE\s*\d*"),
    ("HALL", r"HALL(?:WAY)?\s*\d*"),
    ("ENTRY", r"ENTRY\s*\d*"),
    ("FOYER", r"FOYER\s*\d*"),
    ("STAIR", r"STAIR(?:CASE)?\s*\d*"),
    ("TERRACE", r"TERRACE\s*\d*"),
    ("BALCONY", r"BALCONY\s*\d*"),
    ("CAR PARK", r"CAR\s+PARK\s*\d*"),
    ("CAR PORCH", r"CAR\s+PORCH\s*\d*"),
    ("PARKING", r"PARKING\s*\d*"),
    ("STORE", r"STORE\s*\d*"),
    ("STORAGE", r"STORAGE\s*\d*"),
    ("UTILITY", r"UTILIT(?:Y|IES)\s*\d*"),
    ("WASH", r"WASH\s*\d*"),
    ("VERANDA", r"VERANDA\s*\d*"),
    ("CLOSET", r"(?:WALK[-\s]?IN\s+)?CLOSET\s*\d*"),
    ("PANTRY", r"PANTRY\s*\d*"),
    ("LAUNDRY", r"LAUNDRY\s*\d*"),
]


def get_file_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        return "pdf"
    if name.endswith(".jpg") or name.endswith(".jpeg") or name.endswith(".png"):
        return "image"
    if name.endswith(".dxf"):
        return "dxf"
    if name.endswith(".dwg"):
        return "dwg"
    return "unknown"


def clean_text(text: str) -> str:
    text = text.upper()
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_text(text: str) -> str:
    text = text.upper().strip()
    text = text.replace("’", "'")
    text = re.sub(r"[^A-Z0-9\s\.\-/%&X']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_ocr_text(text: str) -> str:
    text = normalize_text(text)
    replacements = {
        "5Q": "SQ",
        "SQ.FT": "SQ FT",
        "SQ. FT": "SQ FT",
        "SQFT": "SQ FT",
        "SFT": "SQ FT",
        "SF": "SQ FT",
        "FT2": "SQ FT",
        "FT^2": "SQ FT",
        "8ED": "BED",
        "8ATH": "BATH",
        "WALK-IN": "WALK IN",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def ranges_overlap(a_start: float, a_end: float, b_start: float, b_end: float, pad: float = 0.0) -> bool:
    return min(a_end, b_end) + pad >= max(a_start, b_start) - pad


def area_regex_pattern() -> str:
    return r"([0-9]+(?:\.[0-9]+)?)\s*(?:" + "|".join(AREA_UNIT_PATTERNS) + r")"


def canonicalize_room_label(label: str) -> str:
    text = normalize_text(label)
    text = text.replace("WALK IN CLOSET", "WALK-IN CLOSET")
    text = re.sub(r"\bBEDRM\b", "BEDROOM", text)
    text = re.sub(r"\bBED ROOM\b", "BEDROOM", text)
    text = re.sub(r"\bLIVING\b$", "LIVING ROOM", text)
    text = re.sub(r"\bDINING\b$", "DINING ROOM", text)
    text = re.sub(r"\bBATH\b", "BATHROOM", text)
    text = re.sub(r"\bW\.?\s*C\.?\b", "WC", text)
    text = re.sub(r"\bUTILITIES\b", "UTILITY", text)
    text = re.sub(r"\bHALLWAY\b", "HALL", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def best_matching_keyword(text: str, keywords_sorted: list[str]) -> Optional[str]:
    text = normalize_text(text)
    for keyword in keywords_sorted:
        if keyword in text:
            return keyword
    return None


def find_keywords(text: str, keywords: list[str]) -> list[str]:
    text = clean_text(text)
    found = [kw for kw in keywords if kw in text]
    return sorted(set(found))


def extract_room_instances(text: str) -> list[dict[str, str]]:
    cleaned = clean_text(text)
    matches: list[dict[str, Any]] = []

    for room_type, pattern in ROOM_INSTANCE_PATTERNS:
        for match in re.finditer(pattern, cleaned):
            label = canonicalize_room_label(match.group(0))
            if not label:
                continue
            matches.append(
                {
                    "room_type": room_type,
                    "label": label,
                    "start": match.start(),
                    "end": match.end(),
                }
            )

    matches.sort(key=lambda item: (item["start"], -(item["end"] - item["start"])))

    deduped: list[dict[str, Any]] = []
    for item in matches:
        overlaps_existing = False
        for kept in deduped:
            if item["start"] < kept["end"] and item["end"] > kept["start"]:
                overlaps_existing = True
                break
        if not overlaps_existing:
            deduped.append(item)

    return [
        {
            "room_type": str(item["room_type"]),
            "label": str(item["label"]),
        }
        for item in deduped
    ]


def summarize_room_instances(room_instances: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for room in room_instances:
        room_type = room["room_type"]
        counts[room_type] = counts.get(room_type, 0) + 1
    return dict(sorted(counts.items()))


# --- Room area/label extraction helpers ---
def parse_area_sq_ft(text: str) -> Optional[float]:
    cleaned = normalize_ocr_text(text)
    match = re.search(area_regex_pattern(), cleaned)
    if match:
        try:
            return round(float(match.group(1)), 2)
        except ValueError:
            return None
    return None


def match_room_type_from_text(text: str) -> Optional[str]:
    cleaned = normalize_ocr_text(text)
    for room_type, pattern in ROOM_ALIAS_PATTERNS:
        if re.search(pattern, cleaned):
            return room_type
    return None



def extract_room_area_data_from_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    room_data: list[dict[str, Any]] = []

    for line in lines:
        line_text = normalize_text(str(line.get("text", "")))
        if not line_text:
            continue

        room_type = match_room_type_from_text(line_text)
        area_sq_ft = parse_area_sq_ft(line_text)

        if room_type and area_sq_ft is not None:
            room_data.append(
                {
                    "room": room_type,
                    "label": line_text,
                    "width": None,
                    "height": None,
                    "area": area_sq_ft,
                    "area_sq_m": round(area_sq_ft / 10.7639, 2),
                    "unit": "sq_ft",
                    "source": "ocr_room_area_text",
                    "page": line.get("page", 0),
                }
            )

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, float, int]] = set()

    for item in room_data:
        key = (str(item["label"]), float(item["area"]), int(item.get("page", 0)))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


# --- Spatial room/area helpers ---

def line_bounds(line: dict[str, Any]) -> tuple[float, float, float, float]:
    words = line.get("words", [])
    if not words:
        return (0.0, 0.0, 0.0, 0.0)
    min_x = min(float(w["x"]) for w in words)
    min_y = min(float(w["y"]) for w in words)
    max_x = max(float(w["x"]) + float(w["w"]) for w in words)
    max_y = max(float(w["y"]) + float(w["h"]) for w in words)
    return (min_x, min_y, max_x, max_y)


def enrich_line_geometry(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for line in lines:
        min_x, min_y, max_x, max_y = line_bounds(line)
        enriched_line = dict(line)
        enriched_line["min_x"] = min_x
        enriched_line["min_y"] = min_y
        enriched_line["max_x"] = max_x
        enriched_line["max_y"] = max_y
        enriched_line["center_x"] = (min_x + max_x) / 2 if max_x > min_x else min_x
        enriched_line["center_y"] = (min_y + max_y) / 2 if max_y > min_y else min_y
        enriched_line["height"] = max(0.0, max_y - min_y)
        enriched_line["width"] = max(0.0, max_x - min_x)
        enriched_line["text"] = normalize_ocr_text(str(enriched_line.get("text", "")))
        enriched.append(enriched_line)
    return enriched


def line_contains_area_only(text: str) -> bool:
    cleaned = normalize_ocr_text(text)
    return parse_area_sq_ft(cleaned) is not None and match_room_type_from_text(cleaned) is None


def line_contains_room_only(text: str) -> bool:
    cleaned = normalize_ocr_text(text)
    return match_room_type_from_text(cleaned) is not None and parse_area_sq_ft(cleaned) is None


def merge_room_and_area_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = enrich_line_geometry(lines)
    merged: list[dict[str, Any]] = []
    used_indexes: set[int] = set()

    for i, line in enumerate(enriched):
        if i in used_indexes:
            continue

        text = str(line.get("text", ""))
        room_type = match_room_type_from_text(text)
        area_sq_ft = parse_area_sq_ft(text)

        if room_type and area_sq_ft is not None:
            merged.append(line)
            used_indexes.add(i)
            continue

        if not line_contains_room_only(text):
            continue

        best_j: Optional[int] = None
        best_score: Optional[tuple[float, float]] = None

        for j, candidate in enumerate(enriched):
            if j == i or j in used_indexes:
                continue
            if int(candidate.get("page", -1)) != int(line.get("page", -2)):
                continue

            candidate_text = str(candidate.get("text", ""))
            if not line_contains_area_only(candidate_text):
                continue

            vertical_gap = abs(float(candidate["center_y"]) - float(line["center_y"]))
            horizontal_gap = abs(float(candidate["center_x"]) - float(line["center_x"]))
            x_overlap = ranges_overlap(
                float(line["min_x"]),
                float(line["max_x"]),
                float(candidate["min_x"]),
                float(candidate["max_x"]),
                pad=25.0,
            )

            if vertical_gap > 120:
                continue
            if horizontal_gap > 180 and not x_overlap:
                continue

            score = (vertical_gap, horizontal_gap)
            if best_score is None or score < best_score:
                best_score = score
                best_j = j

        if best_j is not None:
            area_line = enriched[best_j]
            combined = dict(line)
            combined_text = normalize_ocr_text(f"{line['text']} {area_line['text']}")
            combined["text"] = combined_text
            combined["words"] = list(line.get("words", [])) + list(area_line.get("words", []))
            min_x, min_y, max_x, max_y = line_bounds(combined)
            combined["min_x"] = min_x
            combined["min_y"] = min_y
            combined["max_x"] = max_x
            combined["max_y"] = max_y
            combined["center_x"] = (min_x + max_x) / 2 if max_x > min_x else min_x
            combined["center_y"] = (min_y + max_y) / 2 if max_y > min_y else min_y
            combined["height"] = max(0.0, max_y - min_y)
            combined["width"] = max(0.0, max_x - min_x)
            merged.append(combined)
            used_indexes.add(i)
            used_indexes.add(best_j)

    for i, line in enumerate(enriched):
        if i not in used_indexes:
            merged.append(line)

    merged.sort(key=lambda item: (int(item.get("page", 0)), float(item.get("center_y", 0.0)), float(item.get("center_x", 0.0))))
    return merged


def extract_room_area_data_spatial(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged_lines = merge_room_and_area_lines(lines)
    room_data: list[dict[str, Any]] = []

    for line in merged_lines:
        text = normalize_ocr_text(str(line.get("text", "")))
        room_type = match_room_type_from_text(text)
        area_sq_ft = parse_area_sq_ft(text)
        if not room_type or area_sq_ft is None:
            continue

        room_data.append(
            {
                "room": room_type,
                "label": text,
                "width": None,
                "height": None,
                "area": area_sq_ft,
                "area_sq_m": round(area_sq_ft / 10.7639, 2),
                "unit": "sq_ft",
                "source": "ocr_spatial_room_area",
                "page": int(line.get("page", 0)),
            }
        )

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, float, int]] = set()
    for item in room_data:
        key = (str(item["label"]), float(item["area"]), int(item.get("page", 0)))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def infer_room_instances_from_room_data(room_data: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, str]], dict[str, int]]:
    inferred_instances: list[dict[str, str]] = []
    inferred_counts: dict[str, int] = {}

    for item in room_data:
        room_type = str(item["room"])
        label = str(item.get("label", room_type))
        inferred_instances.append({"room_type": room_type, "label": label})
        inferred_counts[room_type] = inferred_counts.get(room_type, 0) + 1

    return sorted(inferred_counts.keys()), inferred_instances, dict(sorted(inferred_counts.items()))


def estimate_materials(total_area_sq_ft: float) -> dict[str, int]:
    return {
        "Bricks": int(total_area_sq_ft * 8),
        "Cement Bags": int(total_area_sq_ft * 0.4),
        "Steel (kg)": int(total_area_sq_ft * 4),
        "Floor Tiles (sq ft)": int(total_area_sq_ft * 1.05),
    }


def estimate_costs(total_area_sq_ft: float) -> dict[str, float]:
    base_construction_cost = total_area_sq_ft * 1800
    flooring_cost = total_area_sq_ft * 120
    paint_cost = total_area_sq_ft * 80
    electrical_plumbing_cost = total_area_sq_ft * 250
    total_estimated_cost = (
        base_construction_cost
        + flooring_cost
        + paint_cost
        + electrical_plumbing_cost
    )

    return {
        "Base Construction Cost": round(base_construction_cost, 2),
        "Flooring Cost": round(flooring_cost, 2),
        "Paint Cost": round(paint_cost, 2),
        "Electrical & Plumbing Cost": round(electrical_plumbing_cost, 2),
        "Total Estimated Cost": round(total_estimated_cost, 2),
    }


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            parts.append(txt)
    return "\n".join(parts)


def preprocess_image_for_ocr(pil_image: Image.Image) -> np.ndarray:
    img = np.array(pil_image)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img

    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    processed = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]
    return processed


def ocr_lines_from_images(images: list[Image.Image]) -> tuple[list[dict[str, Any]], str]:
    all_lines: list[dict[str, Any]] = []
    raw_parts: list[str] = []

    for page_index, image in enumerate(images):
        processed = preprocess_image_for_ocr(image)

        ocr = pytesseract.image_to_data(
            processed,
            config="--oem 3 --psm 6",
            output_type=pytesseract.Output.DICT,
        )

        words: list[dict[str, Any]] = []
        for i in range(len(ocr["text"])):
            text = str(ocr["text"][i]).strip()
            if not text:
                continue

            try:
                conf = float(str(ocr["conf"][i]).strip())
            except ValueError:
                conf = -1

            if conf < 25:
                continue

            x = int(ocr["left"][i])
            y = int(ocr["top"][i])
            w = int(ocr["width"][i])
            h = int(ocr["height"][i])

            words.append(
                {
                    "text": normalize_text(text),
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                    "cx": x + w / 2,
                    "cy": y + h / 2,
                    "page": page_index,
                }
            )

        words.sort(key=lambda item: (item["y"], item["x"]))

        lines: list[dict[str, Any]] = []
        y_threshold = 28

        for word in words:
            placed = False
            for line in lines:
                if line["page"] == word["page"] and abs(line["avg_y"] - word["cy"]) <= y_threshold:
                    line["words"].append(word)
                    ys = [w["cy"] for w in line["words"]]
                    line["avg_y"] = sum(ys) / len(ys)
                    placed = True
                    break

            if not placed:
                lines.append(
                    {
                        "page": word["page"],
                        "avg_y": word["cy"],
                        "words": [word],
                    }
                )

    for line in lines:
        line["words"].sort(key=lambda item: item["x"])
        line_text = " ".join(w["text"] for w in line["words"])
        line_text = normalize_ocr_text(line_text)
        line["text"] = line_text
        raw_parts.append(line_text)

        all_lines.extend(lines)

    return all_lines, "\n".join(raw_parts)


def safe_entity_text(entity: Any) -> str:
    try:
        dtype = entity.dxftype()

        if dtype == "TEXT":
            return str(entity.dxf.text)

        if dtype == "MTEXT":
            try:
                return str(entity.plain_text())
            except Exception:
                return str(entity.text)

        if dtype in {"ATTRIB", "ATTDEF"}:
            return str(entity.dxf.text)

        if dtype == "DIMENSION":
            try:
                return str(entity.dxf.text)
            except Exception:
                return ""

        return ""
    except Exception:
        return ""


def extract_insert_texts(entity: Any) -> list[str]:
    texts = []
    try:
        for sub in entity.virtual_entities():
            txt = safe_entity_text(sub)
            if txt:
                texts.append(txt)
    except Exception:
        pass
    return texts


def polyline_points(entity: Any) -> list[tuple[float, float]]:
    points = []

    try:
        dtype = entity.dxftype()

        if dtype == "LWPOLYLINE":
            for p in entity.get_points("xy"):
                points.append((float(p[0]), float(p[1])))

        elif dtype == "POLYLINE":
            for v in entity.vertices:
                loc = v.dxf.location
                points.append((float(loc.x), float(loc.y)))
    except Exception:
        return []

    return points


def safe_polygon_area(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0

    try:
        poly = Polygon(points)
        if poly.is_valid:
            return float(poly.area)
    except Exception:
        pass

    return 0.0


def detect_dxf_unit_to_sqft_factor(doc) -> float:
    """
    Detect the DXF file unit system and return the factor to convert
    one square drawing-unit to sq ft.

    DXF INSUNITS header variable values:
      0  = Unitless (assume mm for Indian architectural drawings)
      1  = Inches
      2  = Feet
      4  = Millimeters
      5  = Centimeters
      6  = Meters
    """
    try:
        insunits = doc.header.get("$INSUNITS", 0)
    except Exception:
        insunits = 0

    # sq ft factors: 1 sq [unit] = X sq ft
    factors = {
        0: 1.0 / 92903.04,   # Unitless → assume mm (most Indian DXFs)
        1: 1.0 / 144.0,      # sq inch → sq ft
        2: 1.0,              # already sq ft
        4: 1.0 / 92903.04,   # sq mm → sq ft
        5: 1.0 / 929.0304,   # sq cm → sq ft
        6: 10.7639,          # sq m → sq ft
    }
    return factors.get(insunits, 1.0 / 92903.04)  # default: mm


def extract_floors_from_text(raw_text: str) -> list[str]:
    floors = []
    for floor in ["GROUND FLOOR", "FIRST FLOOR", "SECOND FLOOR", "TERRACE FLOOR"]:
        if floor in raw_text:
            floors.append(floor)
    return floors


def extract_room_dimension_pairs_from_text(raw_text: str) -> list[dict[str, Any]]:
    room_data = []

    text = raw_text.replace(" X ", "X")
    text = re.sub(r"\s+", " ", text)

    pattern = re.compile(
        r"(" + "|".join(re.escape(k) for k in ROOM_KEYWORDS_SORTED) + r")\s*([0-9]+(?:\.[0-9]+)?)\s*X\s*([0-9]+(?:\.[0-9]+)?)"
    )

    for match in pattern.finditer(text):
        room_name = canonicalize_room_label(match.group(1).strip())
        width = float(match.group(2))
        height = float(match.group(3))
        raw_area = width * height

        # Heuristic: if area > 10000, dimensions are likely in mm not meters
        # 10000 mm² = 0.1 m² which is impossibly small for a room
        # Most Indian DXF room dimensions in mm: e.g. 3600 x 3000 = 10,800,000 mm²
        if raw_area > 10000:
            # Treat as mm²
            area_sq_m = round(raw_area / 1_000_000, 2)
            unit = "mm"
        else:
            # Treat as m²
            area_sq_m = round(raw_area, 2)
            unit = "m"

        area_sq_ft = round(area_sq_m * 10.7639, 2)

        room_data.append(
            {
                "room": room_name,
                "width": width,
                "height": height,
                "area": area_sq_ft,
                "area_sq_m": area_sq_m,
                "unit": unit,
                "source": "dxf_room_dimension_text",
            }
        )

    unique = {}
    for item in room_data:
        key = (item["room"], item["width"], item["height"])
        unique[key] = item

    return list(unique.values())


def assign_floor_to_rooms(raw_text: str, rooms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rooms:
        return rooms

    text = raw_text
    ground_idx = text.find("GROUND FLOOR")
    first_idx = text.find("FIRST FLOOR")

    for room in rooms:
        room["floor"] = None

    if ground_idx != -1 and first_idx != -1:
        ground_chunk = text[ground_idx:first_idx]
        first_chunk = text[first_idx:]

        for room in rooms:
            token = room["room"]
            if token in ground_chunk:
                room["floor"] = "GROUND FLOOR"
            elif token in first_chunk:
                room["floor"] = "FIRST FLOOR"

    elif ground_idx != -1:
        for room in rooms:
            room["floor"] = "GROUND FLOOR"

    return rooms


def extract_area_statement(raw_text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    text = normalize_ocr_text(raw_text)

    # ── Strategy 1: inline number+unit patterns (vector PDFs / clean OCR) ──────
    inline_patterns = {
        "plot_area_sq_ft":        r"PLOT AREA.*?([0-9]+(?:\.[0-9]+)?)\s*(?:SQ\.?\s*FT|SQFT|SFT|SF)(?!\s*SQ)",
        "ground_floor_area_sq_ft":r"(?:PRO\.?\s*)?GROUND FLOOR AREA.*?([0-9]+(?:\.[0-9]+)?)\s*(?:SQ\.?\s*FT|SQFT|SFT|SF)",
        "first_floor_area_sq_ft": r"(?:PRO\.?\s*)?FIRST FLOOR AREA.*?([0-9]+(?:\.[0-9]+)?)\s*(?:SQ\.?\s*FT|SQFT|SFT|SF)",
        "total_fsi_area_sq_ft":   r"TOTAL FSI AREA.*?([0-9]+(?:\.[0-9]+)?)\s*(?:SQ\.?\s*FT|SQFT|SFT|SF)",
        "total_area_sq_ft":       r"(?:NET TOTAL|TOTAL AREA|TOTAL BUILT UP AREA|NET TOTAL FSI).*?([0-9]+(?:\.[0-9]+)?)\s*(?:SQ\.?\s*FT|SQFT|SFT|SF)",
        "plot_area_sq_m":         r"PLOT AREA.*?([0-9]+(?:\.[0-9]+)?)\s*SQ\.?\s*M(?:T|TR)?\b",
        "ground_floor_area_sq_m": r"(?:PRO\.?\s*)?GROUND FLOOR AREA.*?([0-9]+(?:\.[0-9]+)?)\s*SQ\.?\s*M(?:T|TR)?\b",
        "first_floor_area_sq_m":  r"(?:PRO\.?\s*)?FIRST FLOOR AREA.*?([0-9]+(?:\.[0-9]+)?)\s*SQ\.?\s*M(?:T|TR)?\b",
        "total_area_sq_m":        r"(?:NET TOTAL|TOTAL AREA|NET TOTAL FSI).*?([0-9]+(?:\.[0-9]+)?)\s*SQ\.?\s*M(?:T|TR)?\b",
    }
    for key, pattern in inline_patterns.items():
        m = re.search(pattern, text)
        if m:
            try:
                result[key] = float(m.group(1))
            except ValueError:
                pass

    # ── Strategy 2: table format — label then bare number (DXF area statement) ─
    # Handles: "PLOT AREA ( AS PER SITE ) 1000.00 92.90"
    # where the first number is sq ft and second is sq m
    table_patterns = {
        "plot_area_sq_ft":        r"PLOT AREA[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "ground_floor_area_sq_ft":r"(?:PRO\.?\s*)?GROUND FLOOR AREA[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "first_floor_area_sq_ft": r"(?:PRO\.?\s*)?FIRST FLOOR AREA[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "total_fsi_area_sq_ft":   r"TOTAL FSI AREA[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "total_area_sq_ft":       r"NET TOTAL FSI[^0-9]*([0-9]+(?:\.[0-9]+)?)",
    }
    for key, pattern in table_patterns.items():
        if key not in result:  # only fill if Strategy 1 didn't get it
            m = re.search(pattern, text)
            if m:
                try:
                    val = float(m.group(1))
                    # Sanity check: must be a realistic area (10–50000 sq ft)
                    if 10 < val < 50000:
                        result[key] = val
                except ValueError:
                    pass

    return result


def extract_opening_schedule(raw_text: str) -> dict[str, list[dict[str, str]]]:
    doors = []
    windows = []

    text = raw_text

    door_patterns = [
        (r"MAIN DOOR.*?([0-9]+\.[0-9]+X[0-9]+\.[0-9]+)", "MAIN DOOR", "MD"),
        (r"DOOR.*?([0-9]+\.[0-9]+X[0-9]+\.[0-9]+)", "DOOR", "D"),
        (r"TOILET DOOR.*?([0-9]+\.[0-9]+X[0-9]+\.[0-9]+)", "TOILET DOOR", "TD"),
    ]

    for pattern, dtype, tag in door_patterns:
        for m in re.finditer(pattern, text):
            doors.append(
                {
                    "type": dtype,
                    "tag": tag,
                    "size_m": m.group(1),
                }
            )

    size_tokens = re.findall(r"([0-9]+\.[0-9]+X[0-9]+\.[0-9]+)", text)

    if "WINDOW" in text:
        for size in size_tokens[:4]:
            windows.append(
                {
                    "type": "WINDOW",
                    "tag": "W",
                    "size_m": size,
                }
            )

    if "VENTILATOR" in text:
        for size in size_tokens[:2]:
            windows.append(
                {
                    "type": "VENTILATOR",
                    "tag": "V",
                    "size_m": size,
                }
            )

    unique_doors = []
    seen_d = set()
    for d in doors:
        key = (d["type"], d["size_m"])
        if key not in seen_d:
            seen_d.add(key)
            unique_doors.append(d)

    unique_windows = []
    seen_w = set()
    for w in windows:
        key = (w["type"], w["size_m"])
        if key not in seen_w:
            seen_w.add(key)
            unique_windows.append(w)

    return {
        "doors": unique_doors,
        "windows": unique_windows,
    }


def infer_total_area_sq_ft(room_data: list[dict[str, Any]], area_statement: dict[str, Any]) -> float:
    """
    Priority order for total area (most reliable → least reliable):
    1. Net Total FSI & Non FSI (most complete — includes parking, headroom)
    2. Total FSI Area (built-up area only)
    3. Sum of Ground + First floor areas
    4. Sum of individual room areas from room_data
    5. Plot area (last resort)
    """
    # 1. Net total (most complete)
    if "total_area_sq_ft" in area_statement:
        return round(area_statement["total_area_sq_ft"], 2)

    # 2. Total FSI area
    if "total_fsi_area_sq_ft" in area_statement:
        return round(area_statement["total_fsi_area_sq_ft"], 2)

    # 3. Sum floors
    if "ground_floor_area_sq_ft" in area_statement or "first_floor_area_sq_ft" in area_statement:
        return round(
            area_statement.get("ground_floor_area_sq_ft", 0.0)
            + area_statement.get("first_floor_area_sq_ft", 0.0)
            + area_statement.get("second_floor_area_sq_ft", 0.0),
            2,
        )

    # 4. Sum room data (fallback — often incomplete)
    if room_data:
        room_sum = round(sum(float(r["area"]) for r in room_data if r.get("area")), 2)
        if room_sum > 0:
            return room_sum

    # 5. Plot area (last resort — not the built-up area)
    if "plot_area_sq_ft" in area_statement:
        return round(area_statement["plot_area_sq_ft"], 2)

    return 0.0


def build_room_response(raw_text: str) -> tuple[list[str], list[dict[str, str]], dict[str, int]]:
    room_instances = extract_room_instances(raw_text)
    room_types = sorted({room["room_type"] for room in room_instances})

    if not room_types:
        room_types = find_keywords(raw_text, ROOM_KEYWORDS)

    room_counts = summarize_room_instances(room_instances)
    return room_types, room_instances, room_counts


def analyze_pdf(file_bytes: bytes) -> dict[str, Any]:
    pdf_text = clean_text(extract_pdf_text(file_bytes))

    if len(pdf_text) > 20:
        final_text = pdf_text
        method_used = "Direct PDF text extraction"
        room_types_found, room_instances_found, room_counts = build_room_response(final_text)
        features_found = find_keywords(final_text, FEATURE_KEYWORDS)
        room_data = []
        area_statement = extract_area_statement(final_text)
        openings = extract_opening_schedule(final_text)
        floors = extract_floors_from_text(final_text)
        total_area = infer_total_area_sq_ft(room_data, area_statement)
    else:
        images = convert_from_bytes(file_bytes, dpi=500)
        ocr_lines, ocr_text = ocr_lines_from_images(images)
        final_text = ocr_text
        method_used = "OCR fallback with spatial preprocessing"
        room_types_found, room_instances_found, room_counts = build_room_response(final_text)
        features_found = find_keywords(final_text, FEATURE_KEYWORDS)

        room_data = extract_room_area_data_spatial(ocr_lines)
        if not room_data:
            room_data = extract_room_area_data_from_lines(ocr_lines)

        area_statement = extract_area_statement(final_text)
        openings = extract_opening_schedule(final_text)
        floors = extract_floors_from_text(final_text)
        total_area = infer_total_area_sq_ft(room_data, area_statement)

        if room_data:
            inferred_room_types, inferred_instances, inferred_counts = infer_room_instances_from_room_data(room_data)
            if len(inferred_instances) > len(room_instances_found):
                room_types_found = inferred_room_types
                room_instances_found = inferred_instances
                room_counts = inferred_counts

    legacy_result = {
        "source_type": "pdf",
        "method_used": method_used,
        "rooms_found": room_types_found,
        "room_instances_found": room_instances_found,
        "room_counts": room_counts,
        "room_count": len(room_instances_found),
        "features_found": features_found,
        "room_data": room_data,
        "total_area": total_area,
        "materials": estimate_materials(total_area) if total_area > 0 else {},
        "costs": estimate_costs(total_area) if total_area > 0 else {},
        "raw_text": final_text,
        "layers": [],
        "entity_counts": {},
        "block_names": [],
        "block_counts": {},
        "closed_polyline_count": 0,
        "top_polyline_areas": [],
        "floors": floors,
        "area_statement": area_statement,
        "openings": openings,
    }

    if VISION_ENABLED and VISION_AVAILABLE:
        legacy_result["method_used"] = method_used + " + Claude Vision"
        return analyze_pdf_with_vision(file_bytes, legacy_result)
    return legacy_result


def analyze_image(file_bytes: bytes) -> dict[str, Any]:
    image = Image.open(BytesIO(file_bytes)).convert("RGB")
    ocr_lines, ocr_text = ocr_lines_from_images([image])

    room_types_found, room_instances_found, room_counts = build_room_response(ocr_text)
    features_found = find_keywords(ocr_text, FEATURE_KEYWORDS)

    room_data = extract_room_area_data_spatial(ocr_lines)
    if not room_data:
        room_data = extract_room_area_data_from_lines(ocr_lines)

    area_statement = extract_area_statement(ocr_text)
    openings = extract_opening_schedule(ocr_text)
    floors = extract_floors_from_text(ocr_text)
    total_area = infer_total_area_sq_ft(room_data, area_statement)

    if room_data:
        inferred_room_types, inferred_instances, inferred_counts = infer_room_instances_from_room_data(room_data)
        if len(inferred_instances) > len(room_instances_found):
            room_types_found = inferred_room_types
            room_instances_found = inferred_instances
            room_counts = inferred_counts

    legacy_result = {
        "source_type": "image",
        "method_used": "Image OCR with spatial preprocessing",
        "rooms_found": room_types_found,
        "room_instances_found": room_instances_found,
        "room_counts": room_counts,
        "room_count": len(room_instances_found),
        "features_found": features_found,
        "room_data": room_data,
        "total_area": total_area,
        "materials": estimate_materials(total_area) if total_area > 0 else {},
        "costs": estimate_costs(total_area) if total_area > 0 else {},
        "raw_text": ocr_text,
        "layers": [],
        "entity_counts": {},
        "block_names": [],
        "block_counts": {},
        "closed_polyline_count": 0,
        "top_polyline_areas": [],
        "floors": floors,
        "area_statement": area_statement,
        "openings": openings,
    }

    if VISION_ENABLED and VISION_AVAILABLE:
        legacy_result["method_used"] = "Image OCR with spatial preprocessing + Claude Vision"
        return analyze_image_with_vision(file_bytes, legacy_result)
    return legacy_result


def analyze_dxf(file_bytes: bytes) -> dict[str, Any]:
    tmp_path = ""

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        doc = ezdxf.readfile(tmp_path)
        msp = doc.modelspace()

        # Detect drawing units — converts raw polygon area to sq ft
        sqft_factor = detect_dxf_unit_to_sqft_factor(doc)

        layers = [layer.dxf.name for layer in doc.layers]
        entity_counts: dict[str, int] = {}
        block_counts: dict[str, int] = {}
        extracted_texts: list[str] = []
        poly_areas: list[float] = []
        closed_polyline_count = 0

        for entity in msp:
            dtype = entity.dxftype()
            entity_counts[dtype] = entity_counts.get(dtype, 0) + 1

            txt = safe_entity_text(entity)
            if txt:
                extracted_texts.append(txt)

            if dtype == "INSERT":
                try:
                    block_name = str(entity.dxf.name)
                    block_counts[block_name] = block_counts.get(block_name, 0) + 1
                    extracted_texts.extend(extract_insert_texts(entity))
                except Exception:
                    pass

            if dtype in {"LWPOLYLINE", "POLYLINE"}:
                try:
                    is_closed = bool(entity.closed)
                except Exception:
                    is_closed = False

                if is_closed:
                    closed_polyline_count += 1
                    pts = polyline_points(entity)
                    area = safe_polygon_area(pts)
                    if area > 0:
                        area_sqft = round(area * sqft_factor, 2)
                        poly_areas.append(area_sqft)

        raw_text = normalize_ocr_text(clean_text(" ".join(extracted_texts)))

        room_types_found, room_instances_found, room_counts = build_room_response(raw_text)
        features_found = find_keywords(raw_text, FEATURE_KEYWORDS)

        floors = extract_floors_from_text(raw_text)
        room_data = extract_room_dimension_pairs_from_text(raw_text)
        room_data = assign_floor_to_rooms(raw_text, room_data)

        area_statement = extract_area_statement(raw_text)
        openings = extract_opening_schedule(raw_text)

        total_area = infer_total_area_sq_ft(room_data, area_statement)

        block_names = sorted(block_counts.keys())
        top_polyline_areas = sorted(poly_areas, reverse=True)[:10]

        legacy_dxf = {
            "source_type": "dxf",
            "method_used": "DXF CAD entity parsing + domain-specific interpretation",
            "rooms_found": room_types_found,
            "room_instances_found": room_instances_found,
            "room_counts": room_counts,
            "room_count": len(room_instances_found),
            "features_found": features_found,
            "room_data": room_data,
            "total_area": total_area,
            "materials": estimate_materials(total_area) if total_area > 0 else {},
            "costs": estimate_costs(total_area) if total_area > 0 else {},
            "raw_text": raw_text,
            "layers": layers,
            "entity_counts": entity_counts,
            "block_names": block_names,
            "block_counts": block_counts,
            "closed_polyline_count": closed_polyline_count,
            "top_polyline_areas": top_polyline_areas,
            "floors": floors,
            "area_statement": area_statement,
            "openings": openings,
            "note": None,
        }

        if VISION_ENABLED and VISION_AVAILABLE:
            legacy_dxf["method_used"] = "DXF CAD entity parsing + Claude Vision"
            return analyze_dxf_with_vision(file_bytes, legacy_dxf)
        return legacy_dxf

    except Exception as e:
        return {
            "source_type": "dxf",
            "method_used": "DXF parsing failed",
            "rooms_found": [],
            "room_instances_found": [],
            "room_counts": {},
            "room_count": 0,
            "features_found": [],
            "room_data": [],
            "total_area": 0.0,
            "materials": {},
            "costs": {},
            "raw_text": "",
            "layers": [],
            "entity_counts": {},
            "block_names": [],
            "block_counts": {},
            "closed_polyline_count": 0,
            "top_polyline_areas": [],
            "floors": [],
            "area_statement": {},
            "openings": {"doors": [], "windows": []},
            "note": f"DXF parsing failed: {str(e)}",
        }

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def analyze_dwg(file_bytes: bytes) -> dict[str, Any]:
    legacy_dwg = {
        "source_type": "dwg",
        "method_used": "DWG — Claude Vision render attempt",
        "rooms_found": [],
        "room_instances_found": [],
        "room_counts": {},
        "room_count": 0,
        "features_found": [],
        "room_data": [],
        "total_area": 0.0,
        "materials": {},
        "costs": {},
        "raw_text": "",
        "layers": [],
        "entity_counts": {},
        "block_names": [],
        "block_counts": {},
        "closed_polyline_count": 0,
        "top_polyline_areas": [],
        "floors": [],
        "area_statement": {},
        "openings": {"doors": [], "windows": []},
        "note": None,
    }

    if VISION_ENABLED and VISION_AVAILABLE:
        return analyze_dwg_with_vision(file_bytes, legacy_dwg)

    legacy_dwg["note"] = "DWG parsing requires Vision mode. Set VISION_ENABLED=true and add GOOGLE_API_KEY."
    return legacy_dwg


def analyze_blueprint(file_bytes: bytes, filename: str) -> dict[str, Any]:
    file_type = get_file_type(filename)

    if file_type == "pdf":
        return analyze_pdf(file_bytes)
    if file_type == "image":
        return analyze_image(file_bytes)
    if file_type == "dxf":
        return analyze_dxf(file_bytes)
    if file_type == "dwg":
        return analyze_dwg(file_bytes)

    return {
        "source_type": "unknown",
        "method_used": "Unsupported file type",
        "rooms_found": [],
        "room_instances_found": [],
        "room_counts": {},
        "room_count": 0,
        "features_found": [],
        "room_data": [],
        "total_area": 0.0,
        "materials": {},
        "costs": {},
        "raw_text": "",
        "layers": [],
        "entity_counts": {},
        "block_names": [],
        "block_counts": {},
        "closed_polyline_count": 0,
        "top_polyline_areas": [],
        "floors": [],
        "area_statement": {},
        "openings": {"doors": [], "windows": []},
        "note": f"Unsupported file type: {filename}",
    }