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
    "SQ FT", "SQFT", "SFT", "FT2",
]

ROOM_PATTERNS = {
    "MASTER BEDROOM": r"MASTER\\s+BED(?:ROOM)?",
    "BEDROOM": r"BED(?:ROOM|RM)?",
    "LIVING ROOM": r"LIVING(?:\\s+ROOM)?",
    "DINING ROOM": r"DINING(?:\\s+ROOM)?",
    "KITCHEN": r"KITCHEN",
    "BATHROOM": r"BATH(?:ROOM)?",
    "TOILET": r"TOILET",
    "WC": r"W\\.?\\s*C\\.?",
    "LOBBY": r"LOBBY",
    "STAIR": r"STAIR",
    "BALCONY": r"BALCONY",
    "UTILITY": r"UTILITY",
    "STORE": r"STORE",
    "PARKING": r"PARKING",
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
    text = re.sub(r"[^A-Z0-9\\.\\-\\s]", " ", text)
    text = re.sub(r"\\s+", " ", text)
    return text.strip()



def get_file_type(filename: str):
    filename = filename.lower()

    if filename.endswith(".pdf"):
        return "pdf"

    if filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".jpeg"):
        return "image"

    if filename.endswith(".dxf"):
        return "dxf"

    return "unknown"



def parse_area(text: str):
    text = normalize_text(text)

    pattern = r"([0-9]+(?:\\.[0-9]+)?)\\s*(?:SQ FT|SQFT|SFT|FT2)"

    match = re.search(pattern, text)

    if not match:
        return None

    try:
        return float(match.group(1))
    except Exception:
        return None



def match_room(text: str):
    text = normalize_text(text)

    for room, pattern in ROOM_PATTERNS.items():
        if re.search(pattern, text):
            return room

    return None


# =====================================================
# OCR PREPROCESSING
# =====================================================


def preprocess_image_for_ocr(image: Image.Image):
    img = np.array(image)

    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img

    gray = cv2.resize(
        gray,
        None,
        fx=2.5,
        fy=2.5,
        interpolation=cv2.INTER_CUBIC,
    )

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


# =====================================================
# ROOM + AREA MATCHING
# =====================================================


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

            if abs(other["cy"] - word["cy"]) < 30:
                if abs(other["x"] - line_words[-1]["x"]) < 200:
                    line_words.append(other)
                    used.add(j)

        line_words = sorted(line_words, key=lambda x: x["x"])

        text = " ".join(w["text"] for w in line_words)

        phrases.append({
            "text": normalize_text(text),
            "cx": np.mean([w["cx"] for w in line_words]),
            "cy": np.mean([w["cy"] for w in line_words]),
        })

    return phrases



def match_rooms_to_areas(phrases):
    room_labels = []
    area_labels = []

    for phrase in phrases:
        room = match_room(phrase["text"])
        area = parse_area(phrase["text"])

        if room:
            room_labels.append({
                "room": room,
                "text": phrase["text"],
                "cx": phrase["cx"],
                "cy": phrase["cy"],
            })

        if area:
            area_labels.append({
                "area": area,
                "cx": phrase["cx"],
                "cy": phrase["cy"],
            })

    if not room_labels or not area_labels:
        return []

    room_points = [(r["cx"], r["cy"]) for r in room_labels]

    tree = KDTree(room_points)

    room_data = []

    for area in area_labels:
        dist, idx = tree.query((area["cx"], area["cy"]))

        if dist > 250:
            continue

        room = room_labels[idx]

        room_data.append({
            "room": room["room"],
            "label": room["text"],
            "area": area["area"],
            "unit": "sq ft",
            "confidence": 0.88,
            "source": "ocr_spatial_match",
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
                    "area": area,
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
        "Bricks": round(total_area * 8.5),
        "Cement Bags": round(total_area * 0.42),
        "Steel (kg)": round(total_area * 4.2),
        "Sand (cu ft)": round(total_area * 1.8),
        "Aggregate (cu ft)": round(total_area * 1.6),
        "Floor Tiles (sq ft)": round(total_area * 1.08),
        "Paint Area (sq ft)": round(total_area * 3.2),
    }



def estimate_costs(total_area):
    base = total_area * 1800
    flooring = total_area * 120
    paint = total_area * 80
    electrical = total_area * 250

    return {
        "Base Construction Cost": round(base, 2),
        "Flooring Cost": round(flooring, 2),
        "Paint Cost": round(paint, 2),
        "Electrical & Plumbing Cost": round(electrical, 2),
        "Total Estimated Cost": round(
            base + flooring + paint + electrical,
            2,
        )
    }


# =====================================================
# PDF ANALYSIS
# =====================================================


def analyze_pdf(file_bytes: bytes):
    pdf_text = extract_pdf_text(file_bytes)

    images = convert_from_bytes(file_bytes, dpi=300)

    words = extract_ocr_words(images)

    phrases = build_phrases(words)

    room_data = match_rooms_to_areas(phrases)

    final_text = pdf_text + "\n" + "\n".join(p["text"] for p in phrases)

    total_area = sum(r["area"] for r in room_data)

    total_area = validate_total_area(room_data, total_area)

    result = {
        "source_type": "pdf",
        "method_used": "PDF OCR + Spatial Matching",
        "room_data": room_data,
        "total_area": total_area,
        "materials": estimate_materials(total_area),
        "costs": estimate_costs(total_area),
        "raw_text": final_text,
    }

    if VISION_AVAILABLE:
        result = analyze_pdf_with_vision(file_bytes, result)

    return result


# =====================================================
# IMAGE ANALYSIS
# =====================================================


def analyze_image(file_bytes: bytes):
    image = Image.open(BytesIO(file_bytes)).convert("RGB")

    words = extract_ocr_words([image])

    phrases = build_phrases(words)

    room_data = match_rooms_to_areas(phrases)

    total_area = sum(r["area"] for r in room_data)

    total_area = validate_total_area(room_data, total_area)

    result = {
        "source_type": "image",
        "method_used": "Image OCR + Spatial Matching",
        "room_data": room_data,
        "total_area": total_area,
        "materials": estimate_materials(total_area),
        "costs": estimate_costs(total_area),
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

    texts = extract_dxf_texts(msp)

    polygons = extract_closed_room_polygons(msp)

    room_data = []

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
            "room": best_room,
            "area": area_sqft,
            "confidence": 0.98,
            "source": "dxf_geometry",
        })

    total_area = sum(r["area"] for r in room_data)

    result = {
        "source_type": "dxf",
        "method_used": "DXF Geometry + Text Matching",
        "room_data": room_data,
        "total_area": total_area,
        "materials": estimate_materials(total_area),
        "costs": estimate_costs(total_area),
        "raw_text": "\n".join(normalized_texts),
    }

    if VISION_AVAILABLE:
        result = analyze_dxf_with_vision(file_bytes, result)

    return result


# =====================================================
# ENTRY POINT
# =====================================================


def analyze_blueprint(file_bytes: bytes, filename: str):
    file_type = get_file_type(filename)

    if file_type == "pdf":
        return analyze_pdf(file_bytes)

    if file_type == "image":
        return analyze_image(file_bytes)

    if file_type == "dxf":
        return analyze_dxf(file_bytes)

    return {
        "error": "Unsupported file"
    }