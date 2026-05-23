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

# DXF $INSUNITS → multiplier: polygon_area * scale = area in sq ft
# https://help.autodesk.com/view/OARX/2024/en/?guid=GUID-5BE279D0-8E7B-4D8E-9B5E-8E5E5E5E5E5E
INSUNITS_TO_SQFT = {
    0: None,               # unitless — resolved via validate_unit_scale
    1: 1 / 144.0,          # inches → sq ft
    2: 1.0,                # feet
    4: 1 / 92903.04,       # mm² → sq ft
    5: 1 / 929.0304,       # cm² → sq ft
    6: 10.7639,            # m² → sq ft
}

MIN_ROOM_SQFT = 5.0
MAX_ROOM_SQFT = 15000.0
PDF_OCR_DPI = 200
MAX_PDF_PAGES_OCR = 6
MAX_PDF_PAGES_VISION = 4

# Sanity bounds (sq ft) for validation
ROOM_TYPE_BOUNDS = {
    "TOILET": (20, 160),
    "BATHROOM": (20, 160),
    "KITCHEN": (40, 400),
    "BEDROOM": (80, 800),
    "MASTER BEDROOM": (120, 1000),
    "LIVING ROOM": (140, 1500),
    "BALCONY": (15, 300),
    "STORE": (10, 150),
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


def google_api_key() -> str:
    """Read at call time — worker must load .env before importing this module."""
    return (os.environ.get("GOOGLE_API_KEY") or "").strip()


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

try:
    import aspose.cad as cad
    from aspose.cad.imageoptions import DxfOptions
    ASPOSE_CAD_AVAILABLE = True
except ImportError:
    ASPOSE_CAD_AVAILABLE = False

import subprocess
import tempfile

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
    if filename.endswith((".ifc", ".ifczip")):
        return "ifc"
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


def convert_pdf_to_images(file_bytes: bytes, max_pages: int = MAX_PDF_PAGES_OCR):
    """Rasterize PDF for OCR / Vision (requires poppler on server)."""
    return convert_from_bytes(
        file_bytes,
        dpi=PDF_OCR_DPI,
        first_page=1,
        last_page=max_pages,
    )


def extract_ocr_document_text(images) -> str:
    """Full-page OCR text — catches AREA STATEMENT tables on scanned PDFs."""
    if not TESSERACT_AVAILABLE or not images:
        return ""
    parts = []
    configs = ("--oem 3 --psm 6", "--oem 3 --psm 4", "--oem 3 --psm 11")
    for image in images:
        try:
            processed = preprocess_image_for_ocr(image)
            for cfg in configs:
                text = pytesseract.image_to_string(processed, config=cfg)
                if text and len(text.strip()) > 20:
                    parts.append(text)
                    break
        except Exception:
            continue
    return "\n".join(parts)


def ocr_pdf_first_page_hidpi(file_bytes: bytes) -> str:
    """Extra high-DPI pass on page 1 when standard OCR finds little text."""
    if not TESSERACT_AVAILABLE:
        return ""
    try:
        pages = convert_from_bytes(file_bytes, dpi=300, first_page=1, last_page=1)
        if not pages:
            return ""
        return extract_ocr_document_text(pages)
    except Exception:
        return ""


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


def parse_area_statement_totals(text: str) -> dict[str, float]:
    """
    Read official totals from Indian/architect AREA STATEMENT tables on the sheet.
    Values in the SQ.FT column (e.g. NET TOTAL ~1126), not SQ.MT (~104).
    """
    if not text:
        return {}

    blob = fix_ocr_text(text.upper())
    blob = blob.replace("&", " AND ")

    patterns: list[tuple[str, str]] = [
        (r"NET\s+TOTAL\s+FSI(?:\s+AND\s+NON\s+FSI)?\s+AREA\D*(\d+(?:\.\d+)?)", "net_built_up_sqft"),
        (r"NET\s+TOTAL\s+FSI\D*(\d+(?:\.\d+)?)", "net_built_up_sqft"),
        (r"TOTAL\s+FSI\s+AND\s+NON\s+FSI\D*(\d+(?:\.\d+)?)", "net_built_up_sqft"),
        (r"TOTAL\s+FSI\s+AREA\D*(\d+(?:\.\d+)?)", "total_fsi_sqft"),
        (r"PRO\.?\s*GROUND\s+FLOOR\s+AREA\D*(\d+(?:\.\d+)?)", "ground_floor_sqft"),
        (r"PRO\.?\s*FIRST\s+FLOOR\s+AREA\D*(\d+(?:\.\d+)?)", "first_floor_sqft"),
        (r"PRO\.?\s*CAR\s+PARK(?:ING)?\s+AREA\D*(\d+(?:\.\d+)?)", "car_park_sqft"),
        (r"PRO\.?\s*HEAD\s+ROOM\D*(\d+(?:\.\d+)?)", "head_room_sqft"),
        (r"PLOT\s+AREA(?:\s+AS\s+PER\s+\w+)?\D*(\d+(?:\.\d+)?)", "plot_sqft"),
    ]

    found: dict[str, float] = {}
    for pattern, key in patterns:
        if key in found:
            continue
        m = re.search(pattern, blob)
        if m:
            val = float(m.group(1))
            if 50 < val < 50000:
                found[key] = round(val, 2)

    # SQ.MT column misread guard: if "net" looks like sqm (~100), convert
    if "net_built_up_sqft" in found and found["net_built_up_sqft"] < 250:
        sqm_hint = re.search(
            r"NET\s+TOTAL\s+FSI(?:\s+AND\s+NON\s+FSI)?\s+AREA\s+[\d.]+\s+(\d+(?:\.\d+)?)",
            blob,
        )
        if sqm_hint and float(sqm_hint.group(1)) < 250:
            found["net_built_up_sqmt"] = float(sqm_hint.group(1))
            found["net_built_up_sqft"] = round(found["net_built_up_sqmt"] * 10.7639, 2)

    return found


def reconcile_total_with_statement(
    room_data: list[dict],
    room_sum: float,
    raw_text: str,
) -> tuple[list[dict], float, dict[str, float], str]:
    """
    Prefer AREA STATEMENT net total over inflated sum of every closed polygon.
    """
    statement = parse_area_statement_totals(raw_text)
    note = ""

    document_total = (
        statement.get("net_built_up_sqft")
        or statement.get("total_fsi_sqft")
    )
    if not document_total and statement.get("ground_floor_sqft"):
        parts = [
            statement.get("ground_floor_sqft", 0),
            statement.get("first_floor_sqft", 0),
            statement.get("car_park_sqft", 0),
            statement.get("head_room_sqft", 0),
        ]
        parts = [p for p in parts if p]
        if parts:
            document_total = round(sum(parts), 2)

    if not document_total:
        return room_data, round(room_sum, 2), statement, note

    if room_sum > document_total * 1.2:
        factor = document_total / room_sum if room_sum > 0 else 1.0
        scaled = []
        for r in room_data:
            nr = dict(r)
            if nr.get("area"):
                nr["area"] = round(float(nr["area"]) * factor, 2)
                nr["area_adjusted"] = True
            scaled.append(nr)
        room_data = scaled
        note = (
            f"Room areas scaled to match AREA STATEMENT net total "
            f"({document_total} sq ft); geometry sum was {round(room_sum, 2)} sq ft."
        )
        return room_data, document_total, statement, note

    return room_data, round(max(document_total, room_sum), 2), statement, note


def extract_rooms_from_plain_text(text: str) -> list[dict]:
    """Parse embedded PDF text / OCR dump for room + area lines."""
    room_data = []
    if not text or not str(text).strip():
        return room_data

    for raw_line in re.split(r"[\n\r;|]+", text):
        line = normalize_text(raw_line.strip())
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

    # Patterns like "BEDROOM 10' x 12'" on full document blob
    blob = fix_ocr_text(text.upper())
    dim_pat = re.compile(
        r"(MASTER\s+BEDROOM|BEDROOM|LIVING\s+ROOM|DINING\s+ROOM|KITCHEN|"
        r"BATHROOM|TOILET|LOBBY|HALL|BALCONY|UTILITY|PARKING)"
        r".{0,40}?(\d+(?:\.\d+)?)\s*['\u2032]?\s*[xX×]\s*(\d+(?:\.\d+)?)",
        re.IGNORECASE,
    )
    for m in dim_pat.finditer(blob):
        room = match_room(m.group(1))
        if not room:
            continue
        w, h = float(m.group(2)), float(m.group(3))
        # If values are large (e.g. 3800), assume they are mm
        if w > 100 or h > 100:
            area = round((w * h) / 92903.04, 2)
            unit = "sq ft (from mm)"
        else:
            area = round(w * h, 2)
            unit = "sq ft"
            
        room_data.append({
            "room": room,
            "label": m.group(0),
            "area": area,
            "unit": unit,
            "width": w,
            "height": h,
            "floor": detect_floor(m.group(0)),
            "wall_type": None,
            "confidence": 0.8,
            "source": "text_dimensions",
        })

    # Additional pattern for simple "3800 x 2500" without room name inside (nearby search)
    mm_dim_pat = re.compile(r"(\d{3,5})\s*[xX×]\s*(\d{3,5})")
    for m in mm_dim_pat.finditer(blob):
        w, h = float(m.group(1)), float(m.group(2))
        area = round((w * h) / 92903.04, 2)
        room_data.append({
            "room": "UNKNOWN",
            "label": m.group(0),
            "area": area,
            "unit": "sq ft (from mm)",
            "width": w, "height": h,
            "confidence": 0.7,
            "source": "text_dimensions_mm",
        })
    return room_data


def filter_sane_rooms(room_data: list[dict]) -> list[dict]:
    """Drop impossible room areas or those that violate room-type bounds."""
    out = []
    for r in room_data:
        area = float(r.get("area") or 0)
        name = r.get("room", "").upper()
        conf = float(r.get("confidence") or 0)
        source = r.get("source") or ""
        
        if area <= 0:
            if source in ("vision_ai", "ocr_inline", "text_extraction") and conf >= 0.7:
                out.append(r)
            continue
            
        if area < MIN_ROOM_SQFT or area > MAX_ROOM_SQFT:
            continue
            
        # Optional: check type-specific bounds
        for room_type, (min_sqft, max_sqft) in ROOM_TYPE_BOUNDS.items():
            if room_type in name:
                if area < min_sqft * 0.5 or area > max_sqft * 1.5:
                    # Too far off from sanity, likely a scaling error
                    continue
                break
                
        out.append(r)
    return out


def compute_extraction_quality(result: dict) -> dict:
    """Summary scores for UI / debugging reliability."""
    rooms = result.get("room_data") or []
    with_area = [r for r in rooms if float(r.get("area") or 0) > 0]
    total = float(result.get("total_area") or 0)
    avg_conf = (
        sum(float(r.get("confidence") or 0) for r in with_area) / len(with_area)
        if with_area else 0.0
    )
    sources = {r.get("source") for r in rooms if r.get("source")}
    score = 0.0
    if with_area:
        score += 0.45
    if len(with_area) >= 2:
        score += 0.2
    if total >= MIN_TOTAL_SQFT:
        score += 0.2
    if avg_conf >= 0.8:
        score += 0.15
    if result.get("vision_used"):
        score = min(1.0, score + 0.1)
    level = "low"
    if score >= 0.75:
        level = "high"
    elif score >= 0.45:
        level = "medium"
    return {
        "score": round(min(1.0, score), 2),
        "level": level,
        "rooms_with_area": len(with_area),
        "total_rooms": len(rooms),
        "avg_confidence": round(avg_conf, 2),
        "sources": sorted(sources),
    }


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
    return filter_sane_rooms(out)


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
        factor = INSUNITS_TO_SQFT.get(ins)
        if factor is not None:
            return factor
    except Exception:
        pass
    return 1 / 144.0  # default inches when unitless/unknown


def _drawing_span(polygons: list[dict], labels: list[dict]) -> float:
    xs = [p["cx"] for p in polygons] + [l["cx"] for l in labels]
    ys = [p["cy"] for p in polygons] + [l["cy"] for l in labels]
    if not xs:
        return 1.0
    return max(max(xs) - min(xs), max(ys) - min(ys), 1.0)


def filter_room_polygons(polygons: list[dict], span: float) -> list[dict]:
    """Drop site boundary, furniture, and noise polylines."""
    min_draw = (span / 150.0) ** 2
    max_draw = (span * 0.85) ** 2
    return [p for p in polygons if min_draw <= p["area"] <= max_draw]


def resolve_dxf_scale(polygons: list[dict], header_scale: float) -> float:
    """Pick scale so the most polygons look like real rooms (40–2500 sq ft)."""
    if not polygons:
        return header_scale

    candidates = []
    for cand in (
        header_scale,
        1 / 144.0,
        1.0,
        1 / 92903.04,
        1 / 929.0304,
        10.7639,
    ):
        if cand not in candidates and cand > 0:
            candidates.append(cand)

    best_scale = header_scale
    best_score = -1.0

    for cand in candidates:
        sqft = [p["area"] * cand for p in polygons]
        room_like = [a for a in sqft if 40 <= a <= 2500]
        if len(room_like) < 2:
            continue
        med = float(np.median(room_like))
        top_sum = sum(sorted(room_like, reverse=True)[:20])
        score = len(room_like) * 15.0
        score -= abs(med - 140) * 0.05
        if 800 <= top_sum <= 30000:
            score += 80
        elif 400 <= top_sum <= 50000:
            score += 40
        if score > best_score:
            best_score = score
            best_scale = cand

    # NEW: Fallback for huge raw areas (mm) if nothing was 'room-like'
    if best_score < 0:
        raw_areas = [p["area"] for p in polygons]
        if raw_areas:
            med_raw = float(np.median(raw_areas))
            if med_raw > 1000000: # millions of mm2
                best_scale = 1 / 92903.04
                print(f"Fallback to mm-scale (med_raw={med_raw})", flush=True)

    return best_scale


def extract_dxf_text_room_areas(labels: list[dict]) -> list[dict]:
    """Rooms with areas written as CAD text (most reliable for DXF)."""
    room_data = []
    area_only = []

    for lbl in labels:
        room = match_room(lbl["text"])
        area = parse_area(lbl["text"])
        if room and area:
            room_data.append({
                "room": room,
                "label": lbl["text"],
                "area": area,
                "unit": "sq ft",
                "width": None,
                "height": None,
                "floor": detect_floor(lbl["text"]),
                "wall_type": None,
                "confidence": 0.93,
                "source": "dxf_text",
            })
        elif area and not room:
            area_only.append({**lbl, "area": area})

    for lbl in labels:
        room = match_room(lbl["text"])
        if not room or parse_area(lbl["text"]):
            continue
        best_a = None
        best_d = 1e9
        for ao in area_only:
            d = ((lbl["cx"] - ao["cx"]) ** 2 + (lbl["cy"] - ao["cy"]) ** 2) ** 0.5
            if d < best_d:
                best_d = d
                best_a = ao["area"]
        if best_a and best_d < 8000:
            room_data.append({
                "room": room,
                "label": lbl["text"],
                "area": best_a,
                "unit": "sq ft",
                "width": None,
                "height": None,
                "floor": detect_floor(lbl["text"]),
                "wall_type": None,
                "confidence": 0.9,
                "source": "dxf_text_spatial",
            })
    return room_data


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
            points = polyline_points(entity)
            if not points or len(points) < 3:
                continue
            
            # Check if technically closed or visually closed (start == end)
            is_closed = getattr(entity, "closed", False) or getattr(entity.dxf, "flags", 0) & 1
            if not is_closed:
                # Check for visual closure with small tolerance
                d = ((points[0][0] - points[-1][0])**2 + (points[0][1] - points[-1][1])**2)**0.5
                if d < 10.0: # Close enough to be a room
                    is_closed = True
            
            if not is_closed:
                continue
                
            poly = Polygon(points)
            if not poly.is_valid:
                poly = poly.buffer(0) # Attempt to fix self-intersections
            
            if poly.is_empty or poly.area <= 0:
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
        is_inside = False

        for i, lbl in enumerate(labels):
            if i in used_labels:
                continue
            room = match_room(lbl["text"])
            if not room:
                continue

            from shapely.geometry import Point
            p = Point(lbl["cx"], lbl["cy"])
            inside = poly["polygon"].contains(p)
            
            d = ((poly["cx"] - lbl["cx"])**2 + (poly["cy"] - lbl["cy"])**2)**0.5
            
            # Label inside polygon is top priority
            if inside:
                if not is_inside or d < best_dist:
                    best_label = (i, room, lbl)
                    best_dist = d
                    is_inside = True
            elif not is_inside and d < best_dist and d < max_dist:
                best_label = (i, room, lbl)
        text_area = None
        for i, lbl in enumerate(labels):
            a = parse_area(lbl["text"])
            dist = ((poly["cx"] - lbl["cx"])**2 + (poly["cy"] - lbl["cy"])**2)**0.5
            if a and dist < max_dist:
                text_area = a
                break

        if best_label:
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


def validate_total_area(
    room_data: list[dict],
    total_area: float,
    *,
    prefer_document: bool = False,
) -> float:
    room_sum = sum(float(r.get("area") or 0) for r in room_data)
    if total_area <= 0:
        return round(room_sum, 2)
    if prefer_document:
        return round(total_area, 2)
    if room_sum > total_area * 1.2:
        return round(total_area, 2)
    if room_sum > 0 and total_area > room_sum * 1.35:
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

    prefer_doc = bool(result.get("area_statement"))
    total_area = round(
        validate_total_area(
            room_data,
            float(result.get("total_area") or 0),
            prefer_document=prefer_doc,
        ),
        2,
    )

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


def effective_built_up_area(result: dict) -> float:
    """Use documented AREA STATEMENT total; avoid inflating from polygon over-count."""
    if result.get("area_statement", {}).get("net_built_up_sqft"):
        return float(result["area_statement"]["net_built_up_sqft"])
    total = float(result.get("total_area") or 0)
    room_sum = sum(float(r.get("area") or 0) for r in result.get("room_data") or [])
    if room_sum > total * 1.2:
        return round(total, 2)
    if total < MIN_TOTAL_SQFT and room_sum >= MIN_TOTAL_SQFT:
        return round(room_sum, 2)
    return round(max(total, room_sum), 2)


def attach_boq(result: dict) -> dict:
    if not BOQ_AVAILABLE:
        result["notes"] = (result.get("notes") or "") + " BOQ engine unavailable."
        return result
    try:
        area = effective_built_up_area(result)
        if area > float(result.get("total_area") or 0):
            result["total_area"] = area
            result["notes"] = (
                (result.get("notes") or "")
                + " Total area adjusted from room sum for BOQ."
            ).strip()
        boq = generate_boq(result)
        if boq.get("error"):
            result["boq_error"] = boq["error"]
            result["notes"] = (result.get("notes") or "") + f" {boq['error']}"
        else:
            result["boq_items"] = boq.get("items", [])
            result["boq_summary"] = boq.get("summary", {})
            result["boq_total"] = boq.get("grand_total_with_gst") or boq.get("grand_total", 0)
            result["boq_subtotal"] = boq.get("grand_total", 0)
            result["gst_breakdown"] = boq.get("gst_breakdown", {})
            result["cost_per_sqft"] = boq.get("cost_per_sqft", 0)
            result["rates_basis"] = boq.get("rates_basis", "")
            result["rate_schedule"] = boq.get("rate_schedule", "")
            result["building_type"] = boq.get("building_type", "Residential")
            result["area_statement"] = boq.get("area_statement", {})
            result["costs"] = {
                **result.get("costs", {}),
                "Total Estimated Cost": boq.get("grand_total", 0),
            }
    except Exception as exc:
        result["boq_error"] = str(exc)
    return result


def apply_vision_if_needed(file_bytes: bytes, result: dict, analyzer) -> dict:
    """Run Vision when OCR/text found nothing and API key is configured."""
    if not VISION_AVAILABLE or not google_api_key():
        return result
    rooms = result.get("room_data") or []
    has_area = any(float(r.get("area") or 0) > 0 for r in rooms)
    if has_area:
        return result
    try:
        merged = analyzer(file_bytes, result)
        if merged.get("vision_used"):
            merged["method_used"] = (result.get("method_used") or "") + " + Vision AI (fallback)"
        return merged
    except Exception:
        return result


def finalize_result(result: dict) -> dict:
    if result.get("error"):
        return result
    result = enrich_result(result)
    result["extraction_quality"] = compute_extraction_quality(result)
    total_area = float(result.get("total_area") or 0)
    result["materials"] = estimate_materials(total_area)
    if not result.get("boq_items"):
        result["costs"] = estimate_costs(total_area)
    result = attach_boq(result)
    q = result.get("extraction_quality") or {}
    if not result.get("room_data"):
        result["notes"] = (
            (result.get("notes") or "")
            + " No rooms detected. Try a clearer scan, enable Vision API (GOOGLE_API_KEY), or upload DXF."
        ).strip()
        result["error_code"] = result.get("error_code") or "NO_ROOMS_DETECTED"
    elif q.get("level") == "low":
        result["notes"] = (
            (result.get("notes") or "")
            + " Low confidence extraction — verify room areas before using BOQ."
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


def _finalize_raster_result(
    file_bytes: bytes,
    *,
    source_type: str,
    method_parts: list[str],
    room_data: list[dict],
    raw_text: str,
    vision_analyzer,
    notes: str = "",
) -> dict:
    room_sum = sum(float(r.get("area") or 0) for r in room_data)
    room_data, total_area, statement, stmt_note = reconcile_total_with_statement(
        room_data, room_sum, raw_text,
    )
    method = " + ".join(method_parts)
    if statement.get("net_built_up_sqft"):
        method += " + AREA STATEMENT"

    result = {
        "source_type": source_type,
        "method_used": method,
        "room_data": room_data,
        "total_area": total_area,
        "area_statement": statement,
        "raw_text": raw_text,
        "notes": " ".join(x for x in (notes, stmt_note) if x).strip(),
        "tesseract_available": TESSERACT_AVAILABLE,
    }

    has_areas = any(float(r.get("area") or 0) > 0 for r in room_data)
    result["google_api_key_configured"] = bool(google_api_key())
    quota_hit = result.get("vision_error_code") == "QUOTA_EXCEEDED"

    # Vision uses API quota — run when OCR/text found no areas, or always for images
    need_vision = (
        VISION_AVAILABLE
        and google_api_key()
        and not quota_hit
        and (not has_areas or source_type == "image")
    )
    if need_vision:
        result = vision_analyzer(file_bytes, result)
        quota_hit = result.get("vision_error_code") == "QUOTA_EXCEEDED"
        if result.get("vision_used"):
            result["method_used"] += " + Vision AI"
        elif result.get("vision_error"):
            result["method_used"] += " + Vision AI (failed)"
    if VISION_AVAILABLE and google_api_key() and not quota_hit:
        result = apply_vision_if_needed(file_bytes, result, vision_analyzer)

    if result.get("vision_error_code") == "QUOTA_EXCEEDED":
        result["error_code"] = "VISION_QUOTA_EXCEEDED"

    if not TESSERACT_AVAILABLE and not result.get("vision_used"):
        result["notes"] = (
            (result.get("notes") or "")
            + " OCR unavailable on server. Set GOOGLE_API_KEY for Vision analysis."
        ).strip()
    if not google_api_key() and not result.get("vision_used"):
        result["notes"] = (
            (result.get("notes") or "")
            + " GOOGLE_API_KEY not set on worker — PDF/image analysis requires Vision."
        ).strip()

    return finalize_result(result)


def analyze_pdf(file_bytes: bytes) -> dict:
    pdf_text = extract_pdf_text(file_bytes)
    text_rooms = extract_rooms_from_plain_text(pdf_text)
    method_parts = ["PDF extraction"]
    notes = ""

    try:
        images = convert_pdf_to_images(file_bytes)
        method_parts.append(f"OCR ({len(images)} page(s))")
    except Exception as exc:
        notes = f"PDF rasterization failed (install poppler): {exc}"
        images = []
        if VISION_AVAILABLE and google_api_key():
            return _finalize_raster_result(
                file_bytes,
                source_type="pdf",
                method_parts=["PDF text", "Vision AI"],
                room_data=text_rooms,
                raw_text=normalize_text(pdf_text),
                vision_analyzer=analyze_pdf_with_vision,
                notes=notes,
            )
        return finalize_result({
            "source_type": "pdf",
            "method_used": "PDF text only",
            "room_data": text_rooms,
            "total_area": sum(float(r.get("area") or 0) for r in text_rooms),
            "raw_text": normalize_text(pdf_text),
            "notes": notes,
        })

    ocr_blob = extract_ocr_document_text(images)
    if len(ocr_blob.strip()) < 80:
        ocr_blob = (ocr_blob + "\n" + ocr_pdf_first_page_hidpi(file_bytes)).strip()
    words = extract_ocr_words(images)
    phrases = build_phrases(words)
    ocr_rooms = match_rooms_to_areas(phrases)
    text_from_ocr = extract_rooms_from_plain_text(ocr_blob)
    room_data = merge_room_lists(text_rooms, text_from_ocr, ocr_rooms)
    raw_text = normalize_text(
        pdf_text + "\n" + ocr_blob + "\n" + "\n".join(p["text"] for p in phrases),
    )

    return _finalize_raster_result(
        file_bytes,
        source_type="pdf",
        method_parts=method_parts,
        room_data=room_data,
        raw_text=raw_text,
        vision_analyzer=analyze_pdf_with_vision,
        notes=notes,
    )


def analyze_image(file_bytes: bytes) -> dict:
    image = Image.open(BytesIO(file_bytes)).convert("RGB")
    ocr_blob = ""
    words: list[dict] = []
    method_parts = ["Image"]

    if TESSERACT_AVAILABLE:
        method_parts.append("OCR")
        ocr_blob = extract_ocr_document_text([image])
        words = extract_ocr_words([image])

    phrases = build_phrases(words)
    ocr_rooms = match_rooms_to_areas(phrases)
    raw = normalize_text(ocr_blob + "\n" + "\n".join(p["text"] for p in phrases))
    text_rooms = extract_rooms_from_plain_text(raw)
    room_data = merge_room_lists(text_rooms, ocr_rooms)

    return _finalize_raster_result(
        file_bytes,
        source_type="image",
        method_parts=method_parts,
        room_data=room_data,
        raw_text=raw,
        vision_analyzer=analyze_image_with_vision,
    )


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
        span = _drawing_span(polygons, labels)
        polygons = filter_room_polygons(polygons, span)
        header_scale = get_dxf_area_scale(doc)
        scale = resolve_dxf_scale(polygons, header_scale)
        text_rooms = extract_dxf_text_room_areas(labels)
        text_rooms = merge_room_lists(
            text_rooms,
            extract_rooms_from_plain_text("\n".join(l["text"] for l in labels)),
        )
        geom_rooms = match_dxf_polygons_to_labels(polygons, labels, scale)
        room_data = merge_room_lists(text_rooms, geom_rooms)
        raw_text = "\n".join(l["text"] for l in labels)
        room_sum = sum(float(r.get("area") or 0) for r in room_data)
        room_data, total_area, statement, stmt_note = reconcile_total_with_statement(
            room_data, room_sum, raw_text,
        )

        method = f"DXF geometry + label proximity (scale={scale:.6g})"
        if statement.get("net_built_up_sqft"):
            method += " + AREA STATEMENT"

        result = {
            "source_type": "dxf",
            "method_used": method,
            "unit_system": "sq ft",
            "room_data": room_data,
            "total_area": total_area,
            "area_statement": statement,
            "raw_text": raw_text,
            "notes": stmt_note,
        }
        if VISION_AVAILABLE:
            result = analyze_dxf_with_vision(file_bytes, result)
        try:
            from pipelines.plan_engine import enhance_analysis
            result = enhance_analysis(result, dxf_doc=doc, linear_scale=scale)
        except Exception as pipe_exc:
            result["pipeline_warning"] = str(pipe_exc)
        return finalize_result(result)
    finally:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass

def analyze_dwg(file_bytes: bytes) -> dict:
    """
    Handle DWG by converting to DXF. 
    Prioritizes ODA File Converter (Industry Standard) 
    then fallback to LibreDWG or Aspose.CAD.
    """
    import tempfile
    import subprocess
    
    # 1. Try ODA File Converter (Industry Standard for Mac)
    oda_path = "/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter"
    if os.path.exists(oda_path):
        try:
            with tempfile.TemporaryDirectory() as tmp_root:
                input_dir = os.path.join(tmp_root, "in")
                output_dir = os.path.join(tmp_root, "out")
                os.makedirs(input_dir)
                os.makedirs(output_dir)
                
                dwg_file = os.path.join(input_dir, "input.dwg")
                with open(dwg_file, "wb") as f:
                    f.write(file_bytes)
                
                # ODA Arguments: InputDir OutputDir OutVer OutFormat Recurse Audit
                subprocess.run([
                    oda_path, input_dir, output_dir, "ACAD2018", "DXF", "0", "1"
                ], check=True, capture_output=True)
                
                dxf_file = os.path.join(output_dir, "input.dxf")
                if os.path.exists(dxf_file):
                    with open(dxf_file, "rb") as f:
                        dxf_bytes = f.read()
                    res = analyze_dxf(dxf_bytes)
                    res["method_used"] = "dwg_to_dxf_oda"
                    res["notes"] = (res.get("notes") or "") + " (Converted via ODA Engine)"
                    return res
        except Exception as e:
            print(f"ODA Conversion failed: {e}")

    # 2. Try Aspose.CAD (if installed)
    if ASPOSE_CAD_AVAILABLE:
        try:
            with tempfile.NamedTemporaryFile(suffix=".dwg", delete=False) as tf:
                tf.write(file_bytes)
                dwg_path = tf.name
            
            dxf_path = dwg_path.replace(".dwg", ".dxf")
            image = cad.Image.load(dwg_path)
            image.save(dxf_path, DxfOptions())
            
            with open(dxf_path, "rb") as f:
                dxf_bytes = f.read()
            
            os.remove(dwg_path)
            if os.path.exists(dxf_path): os.remove(dxf_path)
            
            res = analyze_dxf(dxf_bytes)
            res["method_used"] = "dwg_to_dxf_aspose"
            return res
        except Exception:
            pass
    
    # 3. Try LibreDWG (installed via Option 1)
    if shutil.which("dwg2dxf"):
        try:
            with tempfile.NamedTemporaryFile(suffix=".dwg", delete=False) as tf:
                tf.write(file_bytes)
                dwg_path = tf.name
            
            dxf_path = dwg_path.replace(".dwg", ".dxf")
            subprocess.run(["dwg2dxf", "-o", dxf_path, dwg_path], check=True, capture_output=True)
            
            with open(dxf_path, "rb") as f:
                dxf_bytes = f.read()
            
            os.remove(dwg_path)
            if os.path.exists(dxf_path): os.remove(dxf_path)
            
            res = analyze_dxf(dxf_bytes)
            res["method_used"] = "dwg_to_dxf_libredwg"
            return res
        except Exception:
            pass

    return {
        "error": "DWG converter not found",
        "error_code": "DEPENDENCY_MISSING",
        "notes": "Please install LibreDWG (Option 1) or ODA File Converter (Option 2) for DWG support.",
    }


def analyze_blueprint(file_bytes: bytes, filename: str) -> dict:
    file_type = get_file_type(filename)

    try:
        if file_type == "pdf":
            return analyze_pdf(file_bytes)
        if file_type == "image":
            return analyze_image(file_bytes)
        if file_type == "dxf":
            return analyze_dxf(file_bytes)
        if file_type == "ifc":
            from pipelines.ifc_parser import analyze_ifc
            ifc_result = analyze_ifc(file_bytes)
            if ifc_result.get("error"):
                return ifc_result
            try:
                from pipelines.plan_engine import enhance_analysis
                ifc_result = enhance_analysis(ifc_result)
            except Exception:
                pass
            return finalize_result(ifc_result)
        if file_type == "dwg":
            return analyze_dwg(file_bytes)
        return {
            "error": "Unsupported file type",
            "error_code": "UNSUPPORTED_FORMAT",
            "notes": "Supported: PDF, JPG, PNG, DXF, IFC.",
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "error_code": "ANALYSIS_FAILED",
            "method_used": file_type,
            "notes": "Analysis failed. Check file integrity and server logs.",
        }
