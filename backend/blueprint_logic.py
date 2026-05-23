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
from scipy.spatial import KDTree
from shapely.geometry import Polygon

print("FINAL BLUEPRINT ENGINE RUNNING", flush=True)

# =====================================================
# CONFIG
# =====================================================

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

# =====================================================
# TESSERACT
# =====================================================

import shutil


def setup_tesseract():
    paths = [
        shutil.which("tesseract"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    for path in paths:
        if path and os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    return False


TESSERACT_AVAILABLE = setup_tesseract()

# =====================================================
# VISION IMPORTS
# =====================================================

try:
    from vision_analyzer import (
        analyze_pdf_with_vision,
        analyze_image_with_vision,
        analyze_dxf_with_vision,
    )
    VISION_AVAILABLE = True
except Exception:
    VISION_AVAILABLE = False

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
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_file_type(filename: str):
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return "pdf"
    if filename.endswith((".png", ".jpg", ".jpeg")):
        return "image"
    if filename.endswith(".dxf"):
        return "dxf"
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
    )
    return gray


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
    all_words = []
    if not TESSERACT_AVAILABLE:
        return all_words

    for page_index, image in enumerate(images):
        processed = preprocess_image_for_ocr(image)

        # Compute the actual scale that preprocess_image_for_ocr applied so we
        # can convert coords back to original image space.
        orig_h = np.array(image).shape[0]
        proc_h = processed.shape[0]
        applied_scale = proc_h / orig_h if orig_h > 0 else 1.0

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
    try:
        reader = PdfReader(BytesIO(file_bytes))
        parts = []
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                parts.append(txt)
        return normalize_text("\n".join(parts))
    except Exception:
        return ""


# =====================================================
# DXF HELPERS
# =====================================================


def polyline_points(entity):
    points = []
    try:
        if entity.dxftype() == "LWPOLYLINE":
            for p in entity.get_points("xy"):
                points.append((float(p[0]), float(p[1])))
    except Exception:
        pass
    return points


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