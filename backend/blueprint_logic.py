import os
import re
<<<<<<< HEAD
import shutil
=======
>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
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

<<<<<<< HEAD
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

MIN_ROOM_SQFT = 15.0
MAX_ROOM_SQFT = 15000.0
MIN_TOTAL_SQFT = 80.0

=======
# BUG FIX #8 (new): File size limit — increase as needed.
# Also update your server/API layer (e.g. FastAPI: app = FastAPI(); set max upload size there).
MAX_FILE_SIZE_MB = 500  # Increased from 100MB to 500MB as requested

ROOM_KEYWORDS = [
    "MASTER BEDROOM", "BEDROOM", "BED ROOM", "BEDRM",
    "LIVING ROOM", "LIVING",
    "DINING ROOM", "DINING",
    "KITCHEN",
    "TOILET", "BATHROOM", "WC",
    "LOBBY", "PASSAGE", "HALL",
    "STAIR", "BALCONY", "TERRACE",
    "UTILITY", "STORE", "PARKING",
]

AREA_UNITS = [
    "SQ FT", "SQFT", "SFT", "FT2", "SF",
]

# BUG FIX #2: Raw strings had double-escaped backslashes (r"MASTER\\s+BED")
# which made \s a literal backslash+s instead of whitespace — so MASTER BEDROOM
# never matched. Fixed to single backslash in raw strings.
ROOM_PATTERNS = {
    "MASTER BEDROOM": r"MASTER\s+BED(?:ROOM)?",
    "BEDROOM":        r"BED(?:ROOM|RM)?",
    "LIVING ROOM":    r"LIVING(?:\s+ROOM)?",
    "DINING ROOM":    r"DINING(?:\s+ROOM)?",
    "KITCHEN":        r"KITCHEN",
    "BATHROOM":       r"BATH(?:ROOM)?",
    "TOILET":         r"TOILET",
    "WC":             r"W\.?\s*C\.?",
    "LOBBY":          r"LOBBY",
    "STAIR":          r"STAIR",
    "BALCONY":        r"BALCONY",
    "UTILITY":        r"UTILITY",
    "STORE":          r"STORE",
    "PARKING":        r"PARKING",
}

>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
# =====================================================
# TESSERACT
# =====================================================

<<<<<<< HEAD

def setup_tesseract():
    for path in (
        shutil.which("tesseract"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ):
=======
import shutil


def setup_tesseract():
    paths = [
        shutil.which("tesseract"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    for path in paths:
>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
        if path and os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    return False


TESSERACT_AVAILABLE = setup_tesseract()

<<<<<<< HEAD
=======
# =====================================================
# VISION IMPORTS
# =====================================================

>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
try:
    from vision_analyzer import (
        analyze_pdf_with_vision,
        analyze_image_with_vision,
        analyze_dxf_with_vision,
    )
    VISION_AVAILABLE = True
except Exception:
    VISION_AVAILABLE = False

<<<<<<< HEAD
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
=======
# =====================================================
# HELPERS
# =====================================================


def normalize_text(text: str) -> str:
    text = text.upper()
    text = text.replace("\n", " ")
    # BUG FIX #1a: Was r"[^A-Z0-9\\.\\-\\s]" — double-escaped \\s is not the
    # whitespace class so spaces were also being removed from normalized text.
    # Fixed: single-escape in raw string gives the correct character class.
    # Keep commas for large numbers (e.g. 1,200 SQFT)
    text = re.sub(r"[^A-Z0-9.\-,\s]", " ", text)
    # BUG FIX #1b: Was r"\\s+" — double-escaped, matched literal \s not whitespace.
>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


<<<<<<< HEAD
def normalize_room_name(room: str) -> str:
    name = normalize_text(room)
    if name in ROOM_NAME_ALIASES:
        return ROOM_NAME_ALIASES[name]
    for canonical, pattern in ROOM_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return canonical
    return name


def get_file_type(filename: str) -> str:
=======
def get_file_type(filename: str):
>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return "pdf"
    if filename.endswith((".png", ".jpg", ".jpeg")):
        return "image"
    if filename.endswith(".dxf"):
        return "dxf"
<<<<<<< HEAD
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
=======
    return "unknown"


def parse_area(text: str):
    # BUG FIX #1c: Was r"([0-9]+(?:\\.[0-9]+)?)\\s*(?:SQ FT|SQFT|SFT|FT2)"
    # Double-escaped \\. and \\s meant the regex never matched area strings in
    # OCR output, so PDF and PNG always returned empty room_data.
    #
    # BUG FIX #7: Expanded pattern to also handle:
    #   - Comma-formatted numbers: 1,200 SQFT
    #   - Short abbreviations: SF, S.F.
    #   - Parenthesised values: (1200 SQFT)
    #   - Flexible spacing between number and unit
    #
    # Strip digit-commas BEFORE normalize_text, because normalize_text replaces
    # every non-alphanumeric char with a space — so "1,200" becomes "1 200"
    # and the regex would match the trailing "200" instead of "1200".
    text = re.sub(r"(\d),(\d)", r"\1\2", text.upper())
    text = normalize_text(text)

    pattern = (
        r"(\d+(?:\.\d+)?)"
        r"\s*"
        r"(?:SQ\.?\s*FT|SQFT|SFT|FT2|SF|S\.F\.)"
    )
    match = re.search(pattern, text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except Exception:
        return None


def match_room(text: str):
    text = normalize_text(text)
    # MASTER BEDROOM must come before BEDROOM so the more-specific pattern wins
    for room, pattern in ROOM_PATTERNS.items():
        if re.search(pattern, text):
            return room
    return None


# =====================================================
# OCR PREPROCESSING
# =====================================================


def preprocess_image_for_ocr(image: Image.Image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if len(img.shape) == 3 else img

    # BUG FIX #5: Was always 2.5× regardless of input resolution.
    # For a 300-DPI PDF page that can be 2500+ px wide, 2.5× creates a ~6250 px
    # image which is very slow and triggers OCR layout errors.
    # For a small PNG it may still be too small.
    # Fix: target ~300 DPI effective height (2400 px); scale only if needed.
    h, w = gray.shape
    TARGET_HEIGHT = 2400
    if h < TARGET_HEIGHT:
        scale = TARGET_HEIGHT / h
        new_w = int(w * scale)
        new_h = TARGET_HEIGHT
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    # If already large enough, leave it — no unnecessary enlargement.

    gray = cv2.fastNlMeansDenoising(gray)
    gray = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2,
>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
    )
    return gray


<<<<<<< HEAD
def extract_ocr_words(images):
=======
# =====================================================
# OCR EXTRACTION
# =====================================================


def extract_ocr_words(images, image_scale: float = 1.0):
    """
    Extract words with bounding boxes from a list of PIL Images.

    image_scale: pass the scale factor applied during preprocess so that
                 returned pixel coordinates reflect the *original* image space,
                 making spatial thresholds consistent across different inputs.
    """
>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
    all_words = []
    if not TESSERACT_AVAILABLE:
        return all_words

    for page_index, image in enumerate(images):
        processed = preprocess_image_for_ocr(image)
<<<<<<< HEAD
=======

        # Compute the actual scale that preprocess_image_for_ocr applied so we
        # can convert coords back to original image space.
        orig_h = np.array(image).shape[0]
        proc_h = processed.shape[0]
        applied_scale = proc_h / orig_h if orig_h > 0 else 1.0

>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
        data = pytesseract.image_to_data(
            processed,
            config="--oem 3 --psm 11 -c preserve_interword_spaces=1",
            output_type=pytesseract.Output.DICT,
        )
<<<<<<< HEAD
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


def filter_sane_rooms(room_data: list[dict]) -> list[dict]:
    """Drop impossible room areas and zero-area rows without a strong source."""
    out = []
    for r in room_data:
        area = float(r.get("area") or 0)
        conf = float(r.get("confidence") or 0)
        source = r.get("source") or ""
        if area <= 0:
            if source in ("vision_ai", "ocr_inline", "text_extraction") and conf >= 0.7:
                out.append(r)
            continue
        if area < MIN_ROOM_SQFT or area > MAX_ROOM_SQFT:
            continue
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
=======

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

            # Convert coords back to original image space for consistent thresholds
            x = int(data["left"][i]   / applied_scale)
            y = int(data["top"][i]    / applied_scale)
            w = int(data["width"][i]  / applied_scale)
            h = int(data["height"][i] / applied_scale)

            all_words.append({
                "text": normalize_text(text),
                "x":  x,
                "y":  y,
                "w":  w,
                "h":  h,
                "cx": x + w / 2,
                "cy": y + h / 2,
                "page": page_index,
            })

    return all_words


# =====================================================
# ROOM + AREA MATCHING
# =====================================================


def build_phrases(words):
    """
    Group OCR words into multi-word phrases.

    BUG FIX #3 — two-pass approach:
      Pass 1: Horizontal grouping (same line, y-diff < 40 px).
              Was 30 px which missed slightly skewed or multi-font lines.
      Pass 2: Vertical stacking — merge adjacent single-line phrases that are
              within 80 px vertically and horizontally overlapping.
              This is critical: blueprints often stack room name + area on two
              separate lines (e.g. "BEDROOM" on line 1, "1200 SQFT" on line 2).
              Without this pass, room labels and area labels were always separate
              phrases, making spatial matching unreliable.
    """
    words = sorted(words, key=lambda x: (x["page"], x["y"], x["x"]))

    # ── Pass 1: horizontal grouping ──────────────────────────────────────────
    lines = []
    used = set()

    for i, word in enumerate(words):
        if i in used:
            continue

        line_words = [word]
        used.add(i)

        for j, other in enumerate(words):
            if j in used:
                continue
            if other["page"] != word["page"]:
                continue
            # BUG FIX #3a: was 30 — increased to 40 for tolerance
            if abs(other["cy"] - word["cy"]) < 40:
                last = line_words[-1]
                gap = other["x"] - (last["x"] + last["w"])
                if gap < 300:   # was 200; increased for wider blueprint labels
                    line_words.append(other)
                    used.add(j)

        line_words = sorted(line_words, key=lambda x: x["x"])
        text = " ".join(w["text"] for w in line_words)

        lines.append({
            "text":  normalize_text(text),
            "cx":    float(np.mean([w["cx"] for w in line_words])),
            "cy":    float(np.mean([w["cy"] for w in line_words])),
            "x_min": min(w["x"] for w in line_words),
            "x_max": max(w["x"] + w["w"] for w in line_words),
            "page":  word["page"],
        })

    # ── Pass 2: vertical stacking ─────────────────────────────────────────────
    # Merge vertically adjacent lines that overlap horizontally.
    # This captures stacked labels like:
    #   BEDROOM          ← line A
    #   1200 SQFT        ← line B  (merged into phrase "BEDROOM 1200 SQFT")
    lines = sorted(lines, key=lambda l: (l["page"], l["cy"]))
    merged_used = set()
    phrases = []

    for i, line_a in enumerate(lines):
        if i in merged_used:
            continue

        combined_text = line_a["text"]
        combined_cx   = [line_a["cx"]]
        combined_cy   = [line_a["cy"]]

        for j, line_b in enumerate(lines):
            if j <= i or j in merged_used:
                continue
            if line_b["page"] != line_a["page"]:
                continue

            v_dist = abs(line_b["cy"] - line_a["cy"])
            # Horizontal overlap check
            h_overlap = (
                line_a["x_min"] < line_b["x_max"] and
                line_b["x_min"] < line_a["x_max"]
            )

            if v_dist < 80 and h_overlap:   # 80 px covers typical line spacing
                combined_text += " " + line_b["text"]
                combined_cx.append(line_b["cx"])
                combined_cy.append(line_b["cy"])
                merged_used.add(j)

        phrases.append({
            "text": normalize_text(combined_text),
            "cx":   float(np.mean(combined_cx)),
            "cy":   float(np.mean(combined_cy)),
        })

    return phrases


def match_rooms_to_areas(phrases):
    room_labels = []
    area_labels = []

    for phrase in phrases:
        room = match_room(phrase["text"])
        area = parse_area(phrase["text"])

        # If a single phrase contains BOTH room name AND area (common after
        # Pass 2 vertical merging), record it directly.
        if room and area:
            room_labels.append({
                "room": room,
                "text": phrase["text"],
                "cx":   phrase["cx"],
                "cy":   phrase["cy"],
                "area": area,          # pre-matched
            })
        else:
            if room:
                room_labels.append({
                    "room": room,
                    "text": phrase["text"],
                    "cx":   phrase["cx"],
                    "cy":   phrase["cy"],
                    "area": None,
                })
            if area:
                area_labels.append({
                    "area": area,
                    "cx":   phrase["cx"],
                    "cy":   phrase["cy"],
                })

    if not room_labels:
        return []

    room_data = []

    # Collect rooms that already have a matched area (from same phrase)
    unmatched_rooms = []
    for r in room_labels:
        if r["area"] is not None:
            room_data.append({
                "room":       r["room"],
                "label":      r["text"],
                "area":       r["area"],
                "unit":       "sq ft",
                "confidence": 0.92,
                "source":     "ocr_same_phrase",
            })
        else:
            unmatched_rooms.append(r)

    # For rooms without a matched area, use KDTree spatial search
    if unmatched_rooms and area_labels:
        room_points = [(r["cx"], r["cy"]) for r in unmatched_rooms]
        tree = KDTree(room_points)

        for area in area_labels:
            # BUG FIX #4: Was 250 px — too tight for large/high-res blueprints.
            # Increased to 500 px to cover typical room-label-to-area spacing.
            dist, idx = tree.query((area["cx"], area["cy"]))
            if dist > 500:
                continue
            room = unmatched_rooms[idx]
            room_data.append({
                "room":       room["room"],
                "label":      room["text"],
                "area":       area["area"],
                "unit":       "sq ft",
                "confidence": 0.88,
                "source":     "ocr_spatial_match",
            })

    return room_data


# =====================================================
# PDF TEXT EXTRACTION
# =====================================================


def extract_pdf_text(file_bytes: bytes):
>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
    try:
        reader = PdfReader(BytesIO(file_bytes))
        parts = []
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                parts.append(txt)
<<<<<<< HEAD
        return "\n".join(parts)
=======
        return normalize_text("\n".join(parts))
>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
    except Exception:
        return ""


# =====================================================
<<<<<<< HEAD
# DXF
# =====================================================


def polyline_points(entity) -> list[tuple[float, float]]:
=======
# DXF HELPERS
# =====================================================


def polyline_points(entity):
>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
    points = []
    try:
        if entity.dxftype() == "LWPOLYLINE":
            for p in entity.get_points("xy"):
                points.append((float(p[0]), float(p[1])))
<<<<<<< HEAD
        elif entity.dxftype() == "POLYLINE":
            for v in entity.vertices:
                points.append((float(v.dxf.location.x), float(v.dxf.location.y)))
=======
>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
    except Exception:
        pass
    return points

<<<<<<< HEAD

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


def apply_vision_if_needed(file_bytes: bytes, result: dict, analyzer) -> dict:
    """Run Vision when OCR/text found nothing and API key is configured."""
    if not VISION_AVAILABLE or not GOOGLE_API_KEY:
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
    raw_text = normalize_text(pdf_text + "\n" + "\n".join(p["text"] for p in phrases))
    room_sum = sum(float(r.get("area") or 0) for r in room_data)
    room_data, total_area, statement, stmt_note = reconcile_total_with_statement(
        room_data, room_sum, raw_text,
    )

    result = {
        "source_type": "pdf",
        "method_used": "PDF text + OCR + spatial matching",
        "room_data": room_data,
        "total_area": total_area,
        "area_statement": statement,
        "raw_text": raw_text,
        "notes": stmt_note,
    }
    if statement.get("net_built_up_sqft"):
        result["method_used"] += " + AREA STATEMENT"

    if VISION_AVAILABLE and GOOGLE_API_KEY:
        result = analyze_pdf_with_vision(file_bytes, result)
        if result.get("vision_used"):
            result["method_used"] += " + Vision AI"
    result = apply_vision_if_needed(file_bytes, result, analyze_pdf_with_vision)

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
    result = apply_vision_if_needed(file_bytes, result, analyze_image_with_vision)

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
=======

def extract_dxf_texts(msp):
    texts = []
    for entity in msp:
        try:
            if entity.dxftype() == "TEXT":
                texts.append(entity.dxf.text)
            elif entity.dxftype() == "MTEXT":
                texts.append(entity.plain_text())
        except Exception:
            continue
    return texts


def extract_closed_room_polygons(msp):
    polygons = []
    for entity in msp:
        if entity.dxftype() not in ["LWPOLYLINE", "POLYLINE"]:
            continue
        try:
            if not entity.closed:
                continue
            points = polyline_points(entity)
            if len(points) < 4:
                continue
            poly = Polygon(points)
            if not poly.is_valid:
                continue
            area = poly.area
            if 20 < area < 100000:
                polygons.append({
                    "polygon": poly,
                    "area":    area,
                    "centroid": poly.centroid,
                })
        except Exception:
            continue
    return polygons


# =====================================================
# VALIDATION
# =====================================================


def validate_total_area(room_data, total_area):
    room_sum = sum(r.get("area", 0) for r in room_data)
    if total_area <= 0:
        return room_sum
    delta = abs(room_sum - total_area)
    if total_area > 0 and delta / total_area > 0.25:
        return room_sum
    return total_area


# =====================================================
# BOQ
# =====================================================


def estimate_materials(total_area):
    return {
        "Bricks":            round(total_area * 8.5),
        "Cement Bags":       round(total_area * 0.42),
        "Steel (kg)":        round(total_area * 4.2),
        "Sand (cu ft)":      round(total_area * 1.8),
        "Aggregate (cu ft)": round(total_area * 1.6),
        "Floor Tiles (sq ft)": round(total_area * 1.08),
        "Paint Area (sq ft)": round(total_area * 3.2),
    }


def estimate_costs(total_area):
    base        = total_area * 1800
    flooring    = total_area * 120
    paint       = total_area * 80
    electrical  = total_area * 250
    return {
        "Base Construction Cost":     round(base, 2),
        "Flooring Cost":              round(flooring, 2),
        "Paint Cost":                 round(paint, 2),
        "Electrical & Plumbing Cost": round(electrical, 2),
        "Total Estimated Cost":       round(base + flooring + paint + electrical, 2),
    }


# =====================================================
# PDF ANALYSIS
# =====================================================


def analyze_pdf(file_bytes: bytes):
    pdf_text = extract_pdf_text(file_bytes)

    # PDF pages are already rendered at 300 DPI — good baseline for OCR.
    images = convert_from_bytes(file_bytes, dpi=300)

    words   = extract_ocr_words(images)
    phrases = build_phrases(words)

    room_data = match_rooms_to_areas(phrases)

    final_text = pdf_text + "\n" + "\n".join(p["text"] for p in phrases)
    total_area = sum(r["area"] for r in room_data)
    total_area = validate_total_area(room_data, total_area)

    result = {
        "source_type": "pdf",
        "method_used": "PDF OCR + Spatial Matching",
        "room_data":   room_data,
        "total_area":  total_area,
        "materials":   estimate_materials(total_area),
        "costs":       estimate_costs(total_area),
        "raw_text":    final_text,
    }

    if VISION_AVAILABLE:
        result = analyze_pdf_with_vision(file_bytes, result)

    return result


# =====================================================
# IMAGE ANALYSIS
# =====================================================


def analyze_image(file_bytes: bytes):
    image = Image.open(BytesIO(file_bytes)).convert("RGB")

    # BUG FIX #6: PDF analysis converts pages at 300 DPI so OCR resolution is
    # consistent. Raw PNG/JPG files have no guaranteed DPI — a scanned blueprint
    # might be 72 DPI (too small) or 600 DPI (already fine).
    # preprocess_image_for_ocr now handles adaptive scaling to ~2400 px height,
    # and returns coords in original image space, so spatial thresholds work.

    words   = extract_ocr_words([image])
    phrases = build_phrases(words)

    room_data  = match_rooms_to_areas(phrases)
    total_area = sum(r["area"] for r in room_data)
    total_area = validate_total_area(room_data, total_area)

    result = {
        "source_type": "image",
        "method_used": "Image OCR + Spatial Matching",
        "room_data":   room_data,
        "total_area":  total_area,
        "materials":   estimate_materials(total_area),
        "costs":       estimate_costs(total_area),
    }

    if VISION_AVAILABLE:
        result = analyze_image_with_vision(file_bytes, result)

    return result


# =====================================================
# DXF ANALYSIS
# =====================================================


def analyze_dxf(file_bytes: bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        tmp.write(file_bytes)
        path = tmp.name

    doc = ezdxf.readfile(path)
    msp = doc.modelspace()

    texts    = extract_dxf_texts(msp)
    polygons = extract_closed_room_polygons(msp)

    room_data        = []
    normalized_texts = [normalize_text(t) for t in texts]

    for poly in polygons:
        best_room = None
        for text in normalized_texts:
            room = match_room(text)
            if room:
                best_room = room
                break
        if not best_room:
            continue

        area_sqft = round(poly["area"] / 144, 2)
        room_data.append({
            "room":       best_room,
            "area":       area_sqft,
            "confidence": 0.98,
            "source":     "dxf_geometry",
        })

    total_area = sum(r["area"] for r in room_data)

    result = {
        "source_type": "dxf",
        "method_used": "DXF Geometry + Text Matching",
        "room_data":   room_data,
        "total_area":  total_area,
        "materials":   estimate_materials(total_area),
        "costs":       estimate_costs(total_area),
        "raw_text":    "\n".join(normalized_texts),
    }

    if VISION_AVAILABLE:
        result = analyze_dxf_with_vision(file_bytes, result)

    return result


# =====================================================
# ENTRY POINT
# =====================================================


def analyze_blueprint(file_bytes: bytes, filename: str):
    # BUG FIX #8: Enforce file size limit before any processing.
    # NOTE: to increase the HTTP upload limit in FastAPI add:
    #   from fastapi import FastAPI
    #   app = FastAPI()
    #   # In your route: use Request directly and read body with size guard, or
    #   # configure your ASGI server (uvicorn --limit-concurrency / nginx client_max_body_size).
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return {
            "error": f"File too large: {size_mb:.1f} MB (max {MAX_FILE_SIZE_MB} MB). "
                     f"Update MAX_FILE_SIZE_MB in blueprint_engine.py and your "
                     f"server upload limit (nginx: client_max_body_size, "
                     f"uvicorn: --limit-max-requests, FastAPI UploadFile)."
        }

    file_type = get_file_type(filename)

    if file_type == "pdf":
        return analyze_pdf(file_bytes)
    if file_type == "image":
        return analyze_image(file_bytes)
    if file_type == "dxf":
        return analyze_dxf(file_bytes)

    return {"error": "Unsupported file type. Supported: .pdf, .png, .jpg, .jpeg, .dxf"}
>>>>>>> a8cb5ed (feat: backend support for PDF/Images and 500MB limit)
