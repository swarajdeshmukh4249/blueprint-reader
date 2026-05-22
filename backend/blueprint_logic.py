import os
import re
import shutil
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
from scipy.spatial import KDTree
from shapely.geometry import Polygon

print("FINAL BLUEPRINT ENGINE RUNNING", flush=True)

# =====================================================
# CONFIG
# =====================================================

ROOM_PATTERNS = [
    ("MASTER BEDROOM", r"MASTER\s+BED(?:\s*ROOM|RM)?"),
    ("BEDROOM", r"(?<!MASTER\s)BED(?:\s*ROOM|RM)?"),
    ("LIVING ROOM", r"LIVING(?:\s+ROOM)?"),
    ("DINING ROOM", r"DINING(?:\s+ROOM)?"),
    ("KITCHEN", r"KITCHEN"),
    ("BATHROOM", r"BATH(?:\s*ROOM)?"),
    ("TOILET", r"TOILET"),
    ("WC", r"W\.?\s*C\.?"),
    ("LOBBY", r"LOBBY"),
    ("PASSAGE", r"PASSAGE"),
    ("HALL", r"HALL"),
    ("STAIR", r"STAIR(?:CASE)?"),
    ("BALCONY", r"BALCONY"),
    ("TERRACE", r"TERRACE"),
    ("UTILITY", r"UTILITY"),
    ("STORE", r"STORE|STORAGE"),
    ("PARKING", r"PARKING|GARAGE"),
    ("LIFT", r"LIFT"),
    ("CORRIDOR", r"CORRIDOR"),
]

FEATURE_KEYWORDS = [
    "STAIR", "BALCONY", "PARKING", "LIFT", "TERRACE", "CORRIDOR", "UTILITY",
]

FLOOR_PATTERNS = [
    (r"GROUND\s*FLOOR|G\.?\s*F\.?|GF\b", "Ground Floor"),
    (r"FIRST\s*FLOOR|1ST\s*FLOOR|FF\b", "First Floor"),
    (r"SECOND\s*FLOOR|2ND\s*FLOOR|SF\b", "Second Floor"),
    (r"TERRACE\s*FLOOR|TF\b", "Terrace Floor"),
]

# OCR misreads → corrected tokens (applied before normalization)
OCR_REPLACEMENTS = [
    (r"\b8ED\s*ROOM\b", "BEDROOM"),
    (r"\b8EDROOM\b", "BEDROOM"),
    (r"\bBED\s*R0OM\b", "BEDROOM"),
    (r"\b5Q\s*FT\b", "SQ FT"),
    (r"\bSQ\s*FT\b", "SQ FT"),
    (r"\bSFT\b", "SQ FT"),
    (r"\bSQFT\b", "SQ FT"),
    (r"\bLIV1NG\b", "LIVING"),
    (r"\bK1TCHEN\b", "KITCHEN"),
    (r"\bBATHR00M\b", "BATHROOM"),
]

AREA_PATTERN = re.compile(
    r"([0-9]+(?:\.[0-9]+)?)\s*(?:SQ\.?\s*FT|SQFT|SFT|FT2|SQ\.?\s*M|SQM|M2)",
    re.IGNORECASE,
)

ROOM_NAME_ALIASES = {
    "BED RM": "BEDROOM",
    "BED ROOM": "BEDROOM",
    "BEDRM": "BEDROOM",
    "MBR": "MASTER BEDROOM",
    "LIVING": "LIVING ROOM",
    "DINING": "DINING ROOM",
    "BATH": "BATHROOM",
    "W C": "WC",
    "W.C.": "WC",
}

# DXF $INSUNITS → multiplier to convert drawing area to sq ft
INSUNITS_TO_SQFT = {
    1: 1 / 144.0,          # inches
    2: 1.0,                # feet
    3: 10.7639,            # meters (area in m² → sq ft)
    4: 1 / 92903.04,       # mm
    5: 10.7639 / 10000,    # cm
    6: 10.7639,            # m
}

# =====================================================
# TESSERACT
# =====================================================


def setup_tesseract():
    for path in (
        shutil.which("tesseract"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ):
        if path and os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    return False


TESSERACT_AVAILABLE = setup_tesseract()

try:
    from vision_analyzer import (
        analyze_pdf_with_vision,
        analyze_image_with_vision,
        analyze_dxf_with_vision,
    )
    VISION_AVAILABLE = True
except Exception:
    VISION_AVAILABLE = False

try:
    from boq_engine import generate_boq
    BOQ_AVAILABLE = True
except Exception:
    BOQ_AVAILABLE = False

# =====================================================
# TEXT HELPERS
# =====================================================


def fix_ocr_text(text: str) -> str:
    t = text.upper()
    for pattern, repl in OCR_REPLACEMENTS:
        t = re.sub(pattern, repl, t, flags=re.IGNORECASE)
    return t


def normalize_text(text: str) -> str:
    text = fix_ocr_text(text.upper())
    text = text.replace("\n", " ")
    text = re.sub(r"[^A-Z0-9.\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_room_name(room: str) -> str:
    name = normalize_text(room)
    if name in ROOM_NAME_ALIASES:
        return ROOM_NAME_ALIASES[name]
    for canonical, pattern in ROOM_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return canonical
    return name


def get_file_type(filename: str) -> str:
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return "pdf"
    if filename.endswith((".png", ".jpg", ".jpeg")):
        return "image"
    if filename.endswith(".dxf"):
        return "dxf"
    if filename.endswith(".dwg"):
        return "dwg"
    return "unknown"


def match_room(text: str) -> Optional[str]:
    text = normalize_text(text)
    for canonical, pattern in ROOM_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return canonical
    return None


def parse_area(text: str) -> Optional[float]:
    text = normalize_text(text)
    match = AREA_PATTERN.search(text)
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    unit = match.group(0).upper()
    if "SQ M" in unit or "SQM" in unit or "M2" in unit:
        return round(value * 10.7639, 2)
    return round(value, 2)


def detect_floor(text: str) -> Optional[str]:
    text = normalize_text(text)
    for pattern, label in FLOOR_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return None


def spatial_label_area_score(room: dict, area: dict) -> float:
    """Lower score = better match (vertical gap weighted, horizontal distance)."""
    dx = abs(room["cx"] - area["cx"])
    dy = abs(room["cy"] - area["cy"])
    rw = room.get("w", 80)
    overlap = max(0, min(room["cx"] + rw, area["cx"] + 40) - max(room["cx"] - rw, area["cx"] - 40))
    overlap_bonus = overlap * 0.15
    return dy * 1.5 + dx * 0.8 - overlap_bonus

# =====================================================
# OCR
# =====================================================


def preprocess_image_for_ocr(image: Image.Image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if len(img.shape) == 3 else img
    gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    gray = cv2.fastNlMeansDenoising(gray)
    gray = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2,
    )
    return gray


def extract_ocr_words(images):
    all_words = []
    if not TESSERACT_AVAILABLE:
        return all_words

    for page_index, image in enumerate(images):
        processed = preprocess_image_for_ocr(image)
        data = pytesseract.image_to_data(
            processed,
            config="--oem 3 --psm 11 -c preserve_interword_spaces=1",
            output_type=pytesseract.Output.DICT,
        )
        for i in range(len(data["text"])):
            text = str(data["text"][i]).strip()
            if not text:
                continue
            try:
                conf = float(data["conf"][i])
            except Exception:
                conf = -1
            if conf < 20:
                continue
            all_words.append({
                "text": normalize_text(text),
                "x": int(data["left"][i]),
                "y": int(data["top"][i]),
                "w": int(data["width"][i]),
                "h": int(data["height"][i]),
                "cx": int(data["left"][i]) + int(data["width"][i]) / 2,
                "cy": int(data["top"][i]) + int(data["height"][i]) / 2,
                "page": page_index,
            })
    return all_words


def build_phrases(words):
    words = sorted(words, key=lambda x: (x["y"], x["x"]))
    phrases = []
    used = set()

    for i, word in enumerate(words):
        if i in used:
            continue
        line_words = [word]
        used.add(i)
        for j, other in enumerate(words):
            if j in used:
                continue
            if abs(other["cy"] - word["cy"]) < 35:
                gap = other["x"] - (line_words[-1]["x"] + line_words[-1].get("w", 0))
                if -20 < gap < 220:
                    line_words.append(other)
                    used.add(j)
        line_words = sorted(line_words, key=lambda x: x["x"])
        text = " ".join(w["text"] for w in line_words)
        phrases.append({
            "text": normalize_text(text),
            "cx": float(np.mean([w["cx"] for w in line_words])),
            "cy": float(np.mean([w["cy"] for w in line_words])),
            "w": sum(w.get("w", 0) for w in line_words),
        })
    return phrases


def match_rooms_to_areas(phrases, max_distance: float = 280):
    room_data = []
    used_areas = set()

    for phrase in phrases:
        room = match_room(phrase["text"])
        area = parse_area(phrase["text"])
        if room and area:
            room_data.append({
                "room": room,
                "label": phrase["text"],
                "area": area,
                "unit": "sq ft",
                "width": None,
                "height": None,
                "floor": detect_floor(phrase["text"]),
                "wall_type": None,
                "confidence": 0.92,
                "source": "ocr_inline",
            })

    room_labels = []
    area_labels = []
    for phrase in phrases:
        room = match_room(phrase["text"])
        area = parse_area(phrase["text"])
        if room and not area:
            room_labels.append({**phrase, "room": room})
        elif area and not room:
            area_labels.append({**phrase, "area": area})

    for area in area_labels:
        best_idx = None
        best_score = max_distance
        for i, room in enumerate(room_labels):
            score = spatial_label_area_score(room, area)
            if score < best_score:
                best_score = score
                best_idx = i
        if best_idx is None:
            continue
        key = (round(area["cx"]), round(area["cy"]))
        if key in used_areas:
            continue
        used_areas.add(key)
        room = room_labels[best_idx]
        room_data.append({
            "room": room["room"],
            "label": room["text"],
            "area": area["area"],
            "unit": "sq ft",
            "width": None,
            "height": None,
            "floor": detect_floor(room["text"] + " " + area["text"]),
            "wall_type": None,
            "confidence": max(0.75, 0.95 - best_score / 600),
            "source": "ocr_spatial_match",
        })

    return dedupe_room_data(room_data)


def extract_rooms_from_plain_text(text: str) -> list[dict]:
    """Parse embedded PDF text / OCR dump for room + area lines."""
    room_data = []
    text = normalize_text(text)
    if not text:
        return room_data

    for line in re.split(r"[\n;|]+", text):
        line = normalize_text(line)
        if len(line) < 4:
            continue
        room = match_room(line)
        area = parse_area(line)
        if room and area:
            room_data.append({
                "room": room,
                "label": line,
                "area": area,
                "unit": "sq ft",
                "width": None,
                "height": None,
                "floor": detect_floor(line),
                "wall_type": None,
                "confidence": 0.85,
                "source": "text_extraction",
            })

    # Patterns like "BEDROOM - 120 SQ FT" or "BEDROOM 10' x 12'"
    dim_pat = re.compile(
        r"(MASTER\s+BEDROOM|BEDROOM|LIVING\s+ROOM|DINING\s+ROOM|KITCHEN|"
        r"BATHROOM|TOILET|LOBBY|HALL|BALCONY|UTILITY|PARKING)"
        r".{0,40}?(\d+(?:\.\d+)?)\s*['\u2032]?\s*[xX×]\s*(\d+(?:\.\d+)?)",
        re.IGNORECASE,
    )
    for m in dim_pat.finditer(text):
        room = match_room(m.group(1))
        if not room:
            continue
        w, h = float(m.group(2)), float(m.group(3))
        room_data.append({
            "room": room,
            "label": m.group(0),
            "area": round(w * h, 2),
            "unit": "sq ft",
            "width": w,
            "height": h,
            "floor": detect_floor(m.group(0)),
            "wall_type": None,
            "confidence": 0.8,
            "source": "text_dimensions",
        })
    return room_data


def dedupe_room_data(room_data: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for r in room_data:
        key = (
            r.get("room"),
            round(float(r.get("area") or 0), 1),
            round(r.get("cx", 0) if "cx" in r else hash(r.get("label", "")), 0),
        )
        if key in seen:
            continue
        seen.add(key)
        r["room"] = normalize_room_name(r["room"])
        out.append(r)
    return out


def merge_room_lists(*sources: list[dict]) -> list[dict]:
    combined = []
    for src in sources:
        combined.extend(src)
    return dedupe_room_data(combined)

# =====================================================
# PDF
# =====================================================


def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_bytes))
        parts = []
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                parts.append(txt)
        return "\n".join(parts)
    except Exception:
        return ""


# =====================================================
# DXF
# =====================================================


def polyline_points(entity) -> list[tuple[float, float]]:
    points = []
    try:
        if entity.dxftype() == "LWPOLYLINE":
            for p in entity.get_points("xy"):
                points.append((float(p[0]), float(p[1])))
        elif entity.dxftype() == "POLYLINE":
            for v in entity.vertices:
                points.append((float(v.dxf.location.x), float(v.dxf.location.y)))
    except Exception:
        pass
    return points


def get_dxf_area_scale(doc) -> float:
    """Return multiplier: drawing_area * scale = sq ft."""
    try:
        ins = int(doc.header.get("$INSUNITS", 0))
        if ins in INSUNITS_TO_SQFT:
            return INSUNITS_TO_SQFT[ins]
    except Exception:
        pass
    return 1 / 144.0  # default inches


def validate_unit_scale(polygons: list[dict], scale: float) -> float:
    """Pick scale so median 'room' area in sq ft is plausible (50–600 sq ft)."""
    if not polygons:
        return scale
    candidates = [scale, 1 / 144.0, 1 / 92903.04, 10.7639]
    best = scale
    best_err = 1e9
    for cand in candidates:
        areas = [p["area"] * cand for p in polygons[:30]]
        if not areas:
            continue
        med = float(np.median(areas))
        if med <= 0:
            continue
        if 50 <= med <= 600:
            return cand
        err = min(abs(med - 120), abs(med - 300))
        if err < best_err:
            best_err = err
            best = cand
    return best


def extract_dxf_text_entities(msp) -> list[dict]:
    entities = []
    for entity in msp:
        try:
            text = None
            x = y = None
            if entity.dxftype() == "TEXT":
                text = entity.dxf.text
                x, y = float(entity.dxf.insert.x), float(entity.dxf.insert.y)
            elif entity.dxftype() == "MTEXT":
                text = entity.plain_text()
                x, y = float(entity.dxf.insert.x), float(entity.dxf.insert.y)
            elif entity.dxftype() == "ATTRIB":
                text = entity.dxf.text
                x, y = float(entity.dxf.insert.x), float(entity.dxf.insert.y)
            if text and x is not None:
                entities.append({
                    "text": normalize_text(str(text)),
                    "x": x, "y": y,
                    "cx": x, "cy": y,
                })
        except Exception:
            continue
    return entities


def extract_closed_room_polygons(msp) -> list[dict]:
    polygons = []
    for entity in msp:
        if entity.dxftype() not in ("LWPOLYLINE", "POLYLINE"):
            continue
        try:
            closed = getattr(entity, "closed", False) or getattr(entity.dxf, "flags", 0) & 1
            if not closed:
                continue
            points = polyline_points(entity)
            if len(points) < 4:
                continue
            poly = Polygon(points)
            if not poly.is_valid or poly.area <= 0:
                continue
            if poly.area < 10:
                continue
            polygons.append({
                "polygon": poly,
                "area": poly.area,
                "centroid": poly.centroid,
                "cx": poly.centroid.x,
                "cy": poly.centroid.y,
            })
        except Exception:
            continue
    return polygons


def _drawing_match_radius(labels: list[dict], polygons: list[dict]) -> float:
    coords = [(p["cx"], p["cy"]) for p in polygons] + [(l["cx"], l["cy"]) for l in labels]
    if len(coords) < 2:
        return 5000.0
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    return max(span * 0.12, 500.0)


def match_dxf_polygons_to_labels(polygons: list[dict], labels: list[dict], scale: float) -> list[dict]:
    room_data = []
    used_labels = set()
    max_dist = _drawing_match_radius(labels, polygons)

    for poly in polygons:
        area_sqft = round(poly["area"] * scale, 2)
        if area_sqft < 15 or area_sqft > 15000:
            continue

        best_label = None
        best_dist = 1e9
        for i, lbl in enumerate(labels):
            if i in used_labels:
                continue
            room = match_room(lbl["text"])
            if not room:
                continue
            dist = ((poly["cx"] - lbl["cx"]) ** 2 + (poly["cy"] - lbl["cy"]) ** 2) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best_label = (i, room, lbl)

        text_area = None
        for lbl in labels:
            a = parse_area(lbl["text"])
            if a and ((poly["cx"] - lbl["cx"]) ** 2 + (poly["cy"] - lbl["cy"]) ** 2) ** 0.5 < best_dist * 1.5:
                text_area = a
                break

        if best_label and best_dist <= max_dist:
            idx, room, lbl = best_label
            used_labels.add(idx)
            final_area = text_area if text_area else area_sqft
            conf = 0.95 if text_area else max(0.7, 0.92 - best_dist / 20000)
            room_data.append({
                "room": room,
                "label": lbl["text"],
                "area": final_area,
                "unit": "sq ft",
                "width": None,
                "height": None,
                "floor": detect_floor(lbl["text"]),
                "wall_type": None,
                "confidence": round(conf, 2),
                "source": "dxf_geometry",
            })
    return room_data

# =====================================================
# VALIDATION & ENRICHMENT
# =====================================================


def validate_total_area(room_data: list[dict], total_area: float) -> float:
    room_sum = sum(float(r.get("area") or 0) for r in room_data)
    if total_area <= 0:
        return round(room_sum, 2)
    if room_sum > 0 and abs(room_sum - total_area) / max(total_area, 1) > 0.35:
        return round(room_sum, 2)
    return round(total_area, 2)


def enrich_result(result: dict) -> dict:
    room_data = result.get("room_data") or []
    rooms_found = sorted({r["room"] for r in room_data if r.get("room")})
    room_counts: dict[str, int] = {}
    for r in room_data:
        name = r.get("room")
        if name:
            room_counts[name] = room_counts.get(name, 0) + 1

    features = set(result.get("features_found") or [])
    for r in room_data:
        if r.get("room") in FEATURE_KEYWORDS:
            features.add(r["room"])
    raw = result.get("raw_text") or ""
    for kw in FEATURE_KEYWORDS:
        if kw in raw.upper():
            features.add(kw)

    floors = {r.get("floor") for r in room_data if r.get("floor")}
    floor_count = max(1, len(floors)) if floors else int(result.get("floor_count") or 1)

    total_area = validate_total_area(room_data, float(result.get("total_area") or 0))

    result.update({
        "drawing_type": result.get("drawing_type") or "Floor Plan",
        "unit_system": result.get("unit_system") or "sq ft",
        "rooms_found": rooms_found,
        "room_instances_found": [r.get("label") or r.get("room") for r in room_data],
        "room_counts": room_counts,
        "room_data": room_data,
        "features_found": sorted(features),
        "floor_count": floor_count,
        "total_area": total_area,
        "openings": result.get("openings") or {"doors": [], "windows": []},
        "vision_confidence": result.get("vision_confidence") or (
            0.75 if result.get("vision_used") else None
        ),
    })
    return result


def attach_boq(result: dict) -> dict:
    if not BOQ_AVAILABLE:
        result["notes"] = (result.get("notes") or "") + " BOQ engine unavailable."
        return result
    try:
        boq = generate_boq(result)
        if boq.get("error"):
            result["boq_error"] = boq["error"]
            result["notes"] = (result.get("notes") or "") + f" {boq['error']}"
        else:
            result["boq_items"] = boq.get("items", [])
            result["boq_summary"] = boq.get("summary", {})
            result["boq_total"] = boq.get("grand_total", 0)
            result["cost_per_sqft"] = boq.get("cost_per_sqft", 0)
            result["rates_basis"] = boq.get("rates_basis", "")
            result["building_type"] = boq.get("building_type", "Residential")
            result["area_statement"] = boq.get("area_statement", {})
            result["costs"] = {
                **result.get("costs", {}),
                "Total Estimated Cost": boq.get("grand_total", 0),
            }
    except Exception as exc:
        result["boq_error"] = str(exc)
    return result


def finalize_result(result: dict) -> dict:
    if result.get("error"):
        return result
    result = enrich_result(result)
    total_area = float(result.get("total_area") or 0)
    result["materials"] = estimate_materials(total_area)
    if not result.get("boq_items"):
        result["costs"] = estimate_costs(total_area)
    result = attach_boq(result)
    if not result.get("room_data"):
        result["notes"] = (
            (result.get("notes") or "")
            + " No rooms detected. Try a clearer scan, enable Vision API, or upload DXF."
        ).strip()
    return result


def estimate_materials(total_area: float) -> dict:
    return {
        "Bricks": round(total_area * 8.5),
        "Cement Bags": round(total_area * 0.42),
        "Steel (kg)": round(total_area * 4.2),
        "Sand (cu ft)": round(total_area * 1.8),
        "Aggregate (cu ft)": round(total_area * 1.6),
        "Floor Tiles (sq ft)": round(total_area * 1.08),
        "Paint Area (sq ft)": round(total_area * 3.2),
    }


def estimate_costs(total_area: float) -> dict:
    base = total_area * 1800
    flooring = total_area * 120
    paint = total_area * 80
    electrical = total_area * 250
    return {
        "Base Construction Cost": round(base, 2),
        "Flooring Cost": round(flooring, 2),
        "Paint Cost": round(paint, 2),
        "Electrical & Plumbing Cost": round(electrical, 2),
        "Total Estimated Cost": round(base + flooring + paint + electrical, 2),
    }

# =====================================================
# ANALYZERS
# =====================================================


def analyze_pdf(file_bytes: bytes) -> dict:
    pdf_text = extract_pdf_text(file_bytes)
    text_rooms = extract_rooms_from_plain_text(pdf_text)

    try:
        images = convert_from_bytes(file_bytes, dpi=300)
    except Exception as exc:
        return finalize_result({
            "source_type": "pdf",
            "method_used": "PDF text only (image conversion failed)",
            "room_data": text_rooms,
            "total_area": sum(r["area"] for r in text_rooms),
            "raw_text": normalize_text(pdf_text),
            "notes": str(exc),
        })

    words = extract_ocr_words(images)
    phrases = build_phrases(words)
    ocr_rooms = match_rooms_to_areas(phrases)
    room_data = merge_room_lists(text_rooms, ocr_rooms)
    total_area = sum(float(r.get("area") or 0) for r in room_data)

    result = {
        "source_type": "pdf",
        "method_used": "PDF text + OCR + spatial matching",
        "room_data": room_data,
        "total_area": total_area,
        "raw_text": normalize_text(pdf_text + "\n" + "\n".join(p["text"] for p in phrases)),
    }

    if VISION_AVAILABLE and GOOGLE_API_KEY:
        result = analyze_pdf_with_vision(file_bytes, result)
        if result.get("vision_used"):
            result["method_used"] += " + Vision AI"

    return finalize_result(result)


def analyze_image(file_bytes: bytes) -> dict:
    image = Image.open(BytesIO(file_bytes)).convert("RGB")
    words = extract_ocr_words([image])
    phrases = build_phrases(words)
    ocr_rooms = match_rooms_to_areas(phrases)
    raw = "\n".join(p["text"] for p in phrases)
    text_rooms = extract_rooms_from_plain_text(raw)
    room_data = merge_room_lists(text_rooms, ocr_rooms)
    total_area = sum(float(r.get("area") or 0) for r in room_data)

    result = {
        "source_type": "image",
        "method_used": "Image OCR + spatial matching",
        "room_data": room_data,
        "total_area": total_area,
        "raw_text": raw,
    }

    if VISION_AVAILABLE and GOOGLE_API_KEY:
        result = analyze_image_with_vision(file_bytes, result)
        if result.get("vision_used"):
            result["method_used"] += " + Vision AI"

    return finalize_result(result)


def analyze_dxf(file_bytes: bytes) -> dict:
    path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            tmp.write(file_bytes)
            path = tmp.name
        doc = ezdxf.readfile(path)
        msp = doc.modelspace()
        labels = extract_dxf_text_entities(msp)
        polygons = extract_closed_room_polygons(msp)
        scale = validate_unit_scale(polygons, get_dxf_area_scale(doc))
        room_data = match_dxf_polygons_to_labels(polygons, labels, scale)
        text_rooms = extract_rooms_from_plain_text("\n".join(l["text"] for l in labels))
        room_data = merge_room_lists(room_data, text_rooms)
        total_area = sum(float(r.get("area") or 0) for r in room_data)

        result = {
            "source_type": "dxf",
            "method_used": f"DXF geometry + label proximity (scale={scale:.6g})",
            "unit_system": "sq ft",
            "room_data": room_data,
            "total_area": total_area,
            "raw_text": "\n".join(l["text"] for l in labels),
        }
        if VISION_AVAILABLE:
            result = analyze_dxf_with_vision(file_bytes, result)
        return finalize_result(result)
    finally:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass


GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


def analyze_blueprint(file_bytes: bytes, filename: str) -> dict:
    file_type = get_file_type(filename)

    try:
        if file_type == "pdf":
            return analyze_pdf(file_bytes)
        if file_type == "image":
            return analyze_image(file_bytes)
        if file_type == "dxf":
            return analyze_dxf(file_bytes)
        if file_type == "dwg":
            return {
                "error": "DWG not supported yet",
                "error_code": "UNSUPPORTED_FORMAT",
                "notes": "Export the drawing as DXF from AutoCAD/Revit, or upload PDF/PNG.",
            }
        return {
            "error": "Unsupported file type",
            "error_code": "UNSUPPORTED_FORMAT",
            "notes": "Supported: PDF, JPG, PNG, DXF.",
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "error_code": "ANALYSIS_FAILED",
            "method_used": file_type,
            "notes": "Analysis failed. Check file integrity and server logs.",
        }
