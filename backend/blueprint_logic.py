import os
import re
import subprocess
import tempfile
from io import BytesIO
from typing import Any, Optional
import shutil

import cv2
import ezdxf
import numpy as np
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from pypdf import PdfReader
from shapely.geometry import Polygon, Point

print("NEW BLUEPRINT LOGIC RUNNING", flush=True)

# ─────────────────────────────────────────────
# Tesseract setup
# ─────────────────────────────────────────────

def _find_and_set_tesseract() -> bool:
    candidates = [
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    ]
    found = shutil.which("tesseract")
    if found:
        candidates.insert(0, found)
    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            pytesseract.pytesseract.tesseract_cmd = path
            print(f"Tesseract found at: {path}", flush=True)
            return True
    print("WARNING: Tesseract not found — OCR disabled, Vision-only mode active", flush=True)
    return False

def _check_tesseract() -> bool:
    if not _find_and_set_tesseract():
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

TESSERACT_AVAILABLE = _check_tesseract()

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

VISION_ENABLED = os.environ.get("VISION_ENABLED", "true").lower() == "true"

# ─────────────────────────────────────────────
# Keywords & Patterns
# ─────────────────────────────────────────────

ROOM_KEYWORDS = [
    "MASTER BEDROOM", "MASTER BED ROOM", "BED ROOM", "BEDROOM", "BEDRM",
    "LIVING ROOM", "LIVING", "SITTING ROOM", "SITTING", "DINING ROOM", "DINING",
    "KITCHEN", "TOILET", "BATHROOM", "BATH ROOM", "BATH", "WC", "W.C.",
    "LOBBY", "PASSAGE", "HALL", "HALLWAY", "ENTRY", "FOYER",
    "STAIR", "STAIRCASE", "TERRACE", "BALCONY",
    "CAR PARK", "CAR PORCH", "PARKING",
    "STORE", "STORE ROOM", "STORAGE", "UTILITY", "UTILITIES",
    "WASH", "WASH ROOM", "VERANDA", "VERANDAH",
    "CLOSET", "WALK IN CLOSET", "WALK-IN CLOSET",
    "PANTRY", "LAUNDRY", "DRAWING ROOM", "FAMILY ROOM",
    "STUDY", "STUDY ROOM", "POOJA", "POOJA ROOM", "PUJA",
    "SERVANT", "SERVANT ROOM", "GUEST ROOM",
    "FRONT PORCH", "PORCH", "GARAGE", "LIFT", "CORRIDOR",
]

FEATURE_KEYWORDS = [
    "GROUND FLOOR", "FIRST FLOOR", "SECOND FLOOR", "THIRD FLOOR",
    "TERRACE", "STAIR", "BALCONY", "PARKING", "CAR PORCH", "PORCH", "ROAD",
    "LIFT", "CORRIDOR",
]

OPENING_KEYWORDS = ["MAIN DOOR", "DOOR", "TOILET DOOR", "WINDOW", "VENTILATOR"]

ROOM_KEYWORDS_SORTED = sorted(ROOM_KEYWORDS, key=len, reverse=True)
FEATURE_KEYWORDS_SORTED = sorted(FEATURE_KEYWORDS, key=len, reverse=True)

ROOM_ALIAS_PATTERNS: list[tuple[str, str]] = [
    ("MASTER BEDROOM", r"MASTER\s+BED(?:\s*ROOM)?"),
    ("BEDROOM", r"BED(?:\s*ROOM|RM)?\s*\d*"),
    ("LIVING ROOM", r"(?:LIVING|DRAWING|FAMILY)(?:\s+ROOM)?"),
    ("SITTING ROOM", r"SITTING(?:\s+ROOM)?"),
    ("DINING ROOM", r"DINING(?:\s+ROOM)?"),
    ("KITCHEN", r"KITCHEN"),
    ("BATHROOM", r"BATH(?:\s*ROOM)?"),
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
    ("STORE", r"STORE(?:\s*ROOM)?"),
    ("STORAGE", r"STORAGE"),
    ("UTILITY", r"UTILIT(?:Y|IES)"),
    ("WASH", r"WASH(?:\s*ROOM)?"),
    ("VERANDA", r"VERAND[AH]"),
    ("CLOSET", r"(?:WALK[-\s]?IN\s+)?CLOSET"),
    ("PANTRY", r"PANTRY"),
    ("LAUNDRY", r"LAUNDRY"),
    ("POOJA ROOM", r"P(?:OO|U)JA(?:\s+ROOM)?"),
    ("SERVANT ROOM", r"SERVANT(?:\s+ROOM)?"),
    ("GUEST ROOM", r"GUEST(?:\s+ROOM)?"),
    ("STUDY ROOM", r"STUDY(?:\s+ROOM)?"),
    ("PORCH", r"(?:FRONT\s+)?PORCH"),
    ("GARAGE", r"GARAGE"),
    ("CORRIDOR", r"CORRIDOR"),
]

ROOM_INSTANCE_PATTERNS: list[tuple[str, str]] = [
    ("MASTER BEDROOM", r"MASTER\s+BED(?:\s*ROOM)?\s*\d*"),
    ("BEDROOM", r"BED(?:\s*ROOM|RM)?\s*\d*"),
    ("LIVING ROOM", r"(?:LIVING|DRAWING|FAMILY)(?:\s+ROOM)?\s*\d*"),
    ("SITTING ROOM", r"SITTING(?:\s+ROOM)?\s*\d*"),
    ("DINING ROOM", r"DINING(?:\s+ROOM)?\s*\d*"),
    ("KITCHEN", r"KITCHEN\s*\d*"),
    ("BATHROOM", r"BATH(?:\s*ROOM)?\s*\d*"),
    ("TOILET", r"TOILET\s*\d*"),
    ("WC", r"W\.?\s*C\.?\s*\d*"),
    ("LOBBY", r"LOBBY\s*\d*"),
    ("PASSAGE", r"PASSAGE\s*\d*"),
    ("HALLWAY", r"HALL(?:WAY)?\s*\d*"),
    ("ENTRY", r"ENTRY\s*\d*"),
    ("FOYER", r"FOYER\s*\d*"),
    ("STAIR", r"STAIR(?:CASE)?\s*\d*"),
    ("TERRACE", r"TERRACE\s*\d*"),
    ("BALCONY", r"BALCONY\s*\d*"),
    ("CAR PARK", r"CAR\s+PARK\s*\d*"),
    ("CAR PORCH", r"CAR\s+PORCH\s*\d*"),
    ("PARKING", r"PARKING\s*\d*"),
    ("STORE", r"STORE(?:\s*ROOM)?\s*\d*"),
    ("STORAGE", r"STORAGE\s*\d*"),
    ("UTILITY", r"UTILIT(?:Y|IES)\s*\d*"),
    ("WASH", r"WASH(?:\s*ROOM)?\s*\d*"),
    ("VERANDA", r"VERAND[AH]\s*\d*"),
    ("CLOSET", r"(?:WALK[-\s]?IN\s+)?CLOSET\s*\d*"),
    ("PANTRY", r"PANTRY\s*\d*"),
    ("LAUNDRY", r"LAUNDRY\s*\d*"),
    ("POOJA ROOM", r"P(?:OO|U)JA(?:\s+ROOM)?\s*\d*"),
    ("SERVANT ROOM", r"SERVANT(?:\s+ROOM)?\s*\d*"),
    ("GUEST ROOM", r"GUEST(?:\s+ROOM)?\s*\d*"),
    ("STUDY ROOM", r"STUDY(?:\s+ROOM)?\s*\d*"),
    ("PORCH", r"(?:FRONT\s+)?PORCH\s*\d*"),
    ("GARAGE", r"GARAGE\s*\d*"),
    ("CORRIDOR", r"CORRIDOR\s*\d*"),
]

AREA_UNIT_PATTERNS = [
    r"SQ\s*\.?\s*FT", r"SQFT", r"SFT", r"SF", r"FT2", r"FT\^2",
    r"SQ\s*FEET", r"SQUARE\s*FEET", r"SQ\.FT",
]

# ─────────────────────────────────────────────
# DWG → DXF Conversion
# ─────────────────────────────────────────────

def convert_dwg_to_dxf_bytes(dwg_bytes: bytes) -> Optional[bytes]:
    with tempfile.TemporaryDirectory() as tmpdir:
        dwg_path = os.path.join(tmpdir, "input.dwg")
        dxf_path = os.path.join(tmpdir, "input.dxf")
        with open(dwg_path, "wb") as f:
            f.write(dwg_bytes)
        try:
            result = subprocess.run(
                ["libreoffice", "--headless", "--norestore",
                 "--convert-to", "dxf", "--outdir", tmpdir, dwg_path],
                capture_output=True, timeout=90,
            )
            if os.path.exists(dxf_path):
                with open(dxf_path, "rb") as f:
                    return f.read()
        except Exception as e:
            print(f"LibreOffice DWG conversion error: {e}", flush=True)
        try:
            doc, _ = ezdxf.recover.readfile(dwg_path)
            out_path = os.path.join(tmpdir, "recovered.dxf")
            doc.saveas(out_path)
            with open(out_path, "rb") as f:
                return f.read()
        except Exception as e:
            print(f"ezdxf DWG recover failed: {e}", flush=True)
    return None

# ─────────────────────────────────────────────
# Text utilities
# ─────────────────────────────────────────────

def get_file_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"): return "pdf"
    if name.endswith((".jpg", ".jpeg", ".png")): return "image"
    if name.endswith(".dxf"): return "dxf"
    if name.endswith(".dwg"): return "dwg"
    return "unknown"

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.upper().replace("\n", " ")).strip()

def normalize_text(text: str) -> str:
    text = text.upper().strip().replace("'", "'")
    text = re.sub(r"[^A-Z0-9\s\.\-/%&X']", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def normalize_ocr_text(text: str) -> str:
    text = normalize_text(text)
    replacements = {
        "5Q": "SQ", "SQ.FT": "SQ FT", "SQ. FT": "SQ FT",
        "SQFT": "SQ FT", "SFT": "SQ FT",
        "FT2": "SQ FT", "FT^2": "SQ FT",
        "8ED": "BED", "8ATH": "BATH",
        "WALK-IN": "WALK IN", "48SQFT": "48 SQ FT",
        "48SQ FT": "48 SQ FT",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    # Fix merged numbers like "48sqft" → "48 SQ FT"
    text = re.sub(r"(\d+)SQ\s*FT", r"\1 SQ FT", text)
    return re.sub(r"\s+", " ", text).strip()

def ranges_overlap(a_start, a_end, b_start, b_end, pad=0.0):
    return min(a_end, b_end) + pad >= max(a_start, b_start) - pad

def area_regex_pattern() -> str:
    return r"([0-9]+(?:\.[0-9]+)?)\s*(?:" + "|".join(AREA_UNIT_PATTERNS) + r")"

def canonicalize_room_label(label: str) -> str:
    text = normalize_text(label)
    text = re.sub(r"\bBEDRM\b", "BEDROOM", text)
    text = re.sub(r"\bBED ROOM\b", "BEDROOM", text)
    text = re.sub(r"\bLIVING\b$", "LIVING ROOM", text)
    text = re.sub(r"\bDINING\b$", "DINING ROOM", text)
    text = re.sub(r"\bBATH\b(?!\s*ROOM)", "BATHROOM", text)
    text = re.sub(r"\bW\.?\s*C\.?\b", "WC", text)
    text = re.sub(r"\bUTILITIES\b", "UTILITY", text)
    text = re.sub(r"\bHALLWAY\b", "HALL", text)
    text = re.sub(r"\bVERANDAH\b", "VERANDA", text)
    text = re.sub(r"\bSTORE ROOM\b", "STORE", text)
    text = re.sub(r"\bWASH ROOM\b", "WASH", text)
    return re.sub(r"\s+", " ", text).strip()

def find_keywords(text, keywords):
    text = clean_text(text)
    return sorted(set(kw for kw in keywords if kw in text))

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

def extract_room_instances(text: str) -> list[dict[str, str]]:
    cleaned = clean_text(text)
    matches: list[dict[str, Any]] = []
    for room_type, pattern in ROOM_INSTANCE_PATTERNS:
        for match in re.finditer(pattern, cleaned):
            label = canonicalize_room_label(match.group(0))
            if not label:
                continue
            matches.append({
                "room_type": room_type, "label": label,
                "start": match.start(), "end": match.end()
            })
    matches.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))
    deduped: list[dict[str, Any]] = []
    for item in matches:
        if not any(item["start"] < k["end"] and item["end"] > k["start"] for k in deduped):
            deduped.append(item)
    return [{"room_type": str(i["room_type"]), "label": str(i["label"])} for i in deduped]

def summarize_room_instances(instances):
    counts: dict[str, int] = {}
    for r in instances:
        counts[r["room_type"]] = counts.get(r["room_type"], 0) + 1
    return dict(sorted(counts.items()))

def build_room_response(raw_text: str):
    instances = extract_room_instances(raw_text)
    types = sorted({r["room_type"] for r in instances})
    if not types:
        types = find_keywords(raw_text, ROOM_KEYWORDS)
    counts = summarize_room_instances(instances)
    return types, instances, counts

def infer_room_instances_from_room_data(room_data):
    instances, counts = [], {}
    for item in room_data:
        rt = str(item["room"])
        label = str(item.get("label", rt))
        instances.append({"room_type": rt, "label": label})
        counts[rt] = counts.get(rt, 0) + 1
    return sorted(counts.keys()), instances, dict(sorted(counts.items()))

# ─────────────────────────────────────────────
# Cost & Material estimation
# ─────────────────────────────────────────────

def estimate_materials(total_area_sq_ft: float) -> dict[str, int]:
    return {
        "Bricks": int(total_area_sq_ft * 8),
        "Cement Bags": int(total_area_sq_ft * 0.4),
        "Steel (kg)": int(total_area_sq_ft * 4),
        "Floor Tiles (sq ft)": int(total_area_sq_ft * 1.05),
        "Sand (cft)": int(total_area_sq_ft * 1.2),
        "Paint (litres)": int(total_area_sq_ft * 0.15),
    }

def estimate_costs(total_area_sq_ft: float) -> dict[str, float]:
    base = total_area_sq_ft * 1800
    flooring = total_area_sq_ft * 120
    paint = total_area_sq_ft * 80
    ep = total_area_sq_ft * 250
    return {
        "Base Construction Cost": round(base, 2),
        "Flooring Cost": round(flooring, 2),
        "Paint Cost": round(paint, 2),
        "Electrical & Plumbing Cost": round(ep, 2),
        "Total Estimated Cost": round(base + flooring + paint + ep, 2),
        "Cost Per Sq Ft": round((base + flooring + paint + ep) / total_area_sq_ft, 2) if total_area_sq_ft > 0 else 0,
    }

# ─────────────────────────────────────────────
# Area statement & openings
# ─────────────────────────────────────────────

def extract_area_statement(raw_text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    text = normalize_ocr_text(raw_text)
    patterns = {
        "plot_area_sq_ft": r"PLOT AREA.*?([0-9]+(?:\.[0-9]+)?)\s*(?:SQ\.?\s*FT|SQFT|SFT|SF)",
        "ground_floor_area_sq_ft": r"GROUND FLOOR AREA.*?([0-9]+(?:\.[0-9]+)?)\s*(?:SQ\.?\s*FT|SQFT|SFT|SF)",
        "first_floor_area_sq_ft": r"FIRST FLOOR AREA.*?([0-9]+(?:\.[0-9]+)?)\s*(?:SQ\.?\s*FT|SQFT|SFT|SF)",
        "total_fsi_area_sq_ft": r"TOTAL FSI AREA.*?([0-9]+(?:\.[0-9]+)?)\s*(?:SQ\.?\s*FT|SQFT|SFT|SF)",
        "total_area_sq_ft": r"(?:NET TOTAL|TOTAL AREA|TOTAL BUILT UP|NET TOTAL FSI).*?([0-9]+(?:\.[0-9]+)?)\s*(?:SQ\.?\s*FT|SQFT|SFT|SF)",
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, text)
        if m:
            try:
                result[key] = float(m.group(1))
            except ValueError:
                pass
    return result

def extract_opening_schedule(raw_text: str) -> dict[str, list[dict[str, str]]]:
    doors, windows = [], []
    door_patterns = [
        (r"MAIN DOOR.*?([0-9]+\.[0-9]+X[0-9]+\.[0-9]+)", "MAIN DOOR", "MD"),
        (r"TOILET DOOR.*?([0-9]+\.[0-9]+X[0-9]+\.[0-9]+)", "TOILET DOOR", "TD"),
        (r"DOOR.*?([0-9]+\.[0-9]+X[0-9]+\.[0-9]+)", "DOOR", "D"),
    ]
    for pattern, dtype, tag in door_patterns:
        for m in re.finditer(pattern, raw_text):
            doors.append({"type": dtype, "tag": tag, "size_m": m.group(1)})
    size_tokens = re.findall(r"([0-9]+\.[0-9]+X[0-9]+\.[0-9]+)", raw_text)
    if "WINDOW" in raw_text:
        for size in size_tokens[:4]:
            windows.append({"type": "WINDOW", "tag": "W", "size_m": size})
    if "VENTILATOR" in raw_text:
        for size in size_tokens[:2]:
            windows.append({"type": "VENTILATOR", "tag": "V", "size_m": size})
    return {
        "doors": list({(d["type"], d["size_m"]): d for d in doors}.values()),
        "windows": list({(w["type"], w["size_m"]): w for w in windows}.values()),
    }

def extract_floors_from_text(raw_text: str) -> list[str]:
    return [f for f in ["GROUND FLOOR", "FIRST FLOOR", "SECOND FLOOR", "TERRACE FLOOR"] if f in raw_text]

def infer_total_area_sq_ft(room_data, area_statement) -> float:
    if "total_area_sq_ft" in area_statement:
        return round(area_statement["total_area_sq_ft"], 2)
    if "total_fsi_area_sq_ft" in area_statement:
        return round(area_statement["total_fsi_area_sq_ft"], 2)
    if "ground_floor_area_sq_ft" in area_statement or "first_floor_area_sq_ft" in area_statement:
        return round(
            area_statement.get("ground_floor_area_sq_ft", 0.0) +
            area_statement.get("first_floor_area_sq_ft", 0.0) +
            area_statement.get("second_floor_area_sq_ft", 0.0), 2)
    if room_data:
        s = round(sum(float(r["area"]) for r in room_data if r.get("area") and float(r["area"]) > 0), 2)
        if s > 0:
            return s
    if "plot_area_sq_ft" in area_statement:
        return round(area_statement["plot_area_sq_ft"], 2)
    return 0.0

# ─────────────────────────────────────────────
# OCR preprocessing
# ─────────────────────────────────────────────

def preprocess_image_for_ocr(pil_image: Image.Image) -> np.ndarray:
    img = np.array(pil_image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if len(img.shape) == 3 else img
    h, w = gray.shape[:2]
    # Scale up if small, 2x for normal images
    scale = 2 if max(h, w) < 3000 else 1
    if scale > 1:
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    # Simple binary threshold — best for blueprint text
    _, gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return gray

# ─────────────────────────────────────────────
# Core OCR: proximity-based room-area matcher
# ─────────────────────────────────────────────

def extract_rooms_from_ocr_data(ocr_data: dict) -> list[dict[str, Any]]:
    """
    Proximity-based matcher: for each area label found,
    find the nearest room name above or at same level.
    This is the key algorithm that correctly pairs room names with areas.
    """
    words = []
    for i in range(len(ocr_data["text"])):
        text = str(ocr_data["text"][i]).strip()
        try:
            conf = float(str(ocr_data["conf"][i]).strip())
        except ValueError:
            conf = -1
        if not text or conf < 20:
            continue
        words.append({
            "text": normalize_text(text),
            "x": int(ocr_data["left"][i]),
            "y": int(ocr_data["top"][i]),
            "w": int(ocr_data["width"][i]),
            "h": int(ocr_data["height"][i]),
            "cx": int(ocr_data["left"][i]) + int(ocr_data["width"][i]) / 2,
            "cy": int(ocr_data["top"][i]) + int(ocr_data["height"][i]) / 2,
        })

    # Group words into lines by y-proximity
    words_sorted = sorted(words, key=lambda w: (w["y"], w["x"]))
    lines = []
    used = set()
    for i, word in enumerate(words_sorted):
        if i in used:
            continue
        line_words = [word]
        used.add(i)
        for j, other in enumerate(words_sorted):
            if j in used:
                continue
            if abs(other["cy"] - word["cy"]) <= 15:
                line_words.append(other)
                used.add(j)
        line_words.sort(key=lambda w: w["x"])
        # Merge only words that are close horizontally
        phrases = []
        current = [line_words[0]]
        for lw in line_words[1:]:
            gap = lw["x"] - (current[-1]["x"] + current[-1]["w"])
            if gap < 120:
                current.append(lw)
            else:
                phrases.append(current)
                current = [lw]
        phrases.append(current)

        for phrase in phrases:
            text = normalize_ocr_text(" ".join(w["text"] for w in phrase))
            cx = sum(w["cx"] for w in phrase) / len(phrase)
            cy = sum(w["cy"] for w in phrase) / len(phrase)
            lines.append({"text": text, "cx": cx, "cy": cy, "words": phrase})

    # Separate room labels and area labels
    room_labels = []
    area_labels = []
    for line in lines:
        room = match_room_type_from_text(line["text"])
        area = parse_area_sq_ft(line["text"])
        if room:
            room_labels.append({**line, "room": room})
        if area:
            area_labels.append({**line, "area": area})

    # For each area label, find closest room label above it or nearby
    room_data = []
    used_rooms = set()
    for area in area_labels:
        best = None
        best_dist = float("inf")
        for j, room in enumerate(room_labels):
            if j in used_rooms:
                continue
            dy = area["cy"] - room["cy"]  # positive = room is above area
            dx = abs(area["cx"] - room["cx"])
            # Room must be above area or at same level (not more than 20px below)
            if dy < -20:
                continue
            # Distance formula: horizontal matters more than vertical
            dist = dx * 1.0 + max(0, dy) * 0.3
            if dist < best_dist and dist < 600:
                best_dist = dist
                best = (j, room)

        if best:
            j, room = best
            used_rooms.add(j)
            area_sq_ft = area["area"]
            room_data.append({
                "room": room["room"],
                "label": room["text"],
                "width": None, "height": None,
                "area": area_sq_ft,
                "area_sq_m": round(area_sq_ft / 10.7639, 2),
                "unit": "sq_ft",
                "source": "proximity_ocr",
                "page": 0,
            })

    print(f"Proximity matcher found {len(room_data)} rooms", flush=True)
    return room_data


def run_ocr_on_image(pil_image: Image.Image) -> tuple[dict, str]:
    """Run OCR and return both raw dict (for proximity matching) and text string."""
    processed = preprocess_image_for_ocr(pil_image)
    ocr_data = pytesseract.image_to_data(
        processed, config="--oem 3 --psm 3",
        output_type=pytesseract.Output.DICT
    )
    # Build raw text for keyword extraction
    words = [str(t).strip() for t, c in zip(ocr_data["text"], ocr_data["conf"])
             if str(t).strip() and float(str(c)) > 20]
    raw_text = normalize_ocr_text(" ".join(words))
    return ocr_data, raw_text


# ─────────────────────────────────────────────
# PDF text extraction
# ─────────────────────────────────────────────

def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_bytes))
        parts = [page.extract_text() for page in reader.pages if page.extract_text()]
        return "\n".join(parts)
    except Exception:
        return ""

# ─────────────────────────────────────────────
# DXF utilities
# ─────────────────────────────────────────────

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
    except Exception:
        pass
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
        pass
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
    try:
        insunits = doc.header.get("$INSUNITS", 0)
    except Exception:
        insunits = 0
    factors = {
        0: 1.0 / 92903.04,
        1: 1.0 / 144.0,
        2: 1.0,
        4: 1.0 / 92903.04,
        5: 1.0 / 929.0304,
        6: 10.7639,
    }
    return factors.get(insunits, 1.0 / 92903.04)

def validate_unit_factor(poly_areas_raw: list[float], factor: float) -> float:
    if not poly_areas_raw:
        return factor
    test_areas = [a * factor for a in poly_areas_raw if a > 0]
    realistic = [a for a in test_areas if 10 < a < 5000]
    if test_areas and len(realistic) / len(test_areas) > 0.5:
        return factor
    mm_factor = 1.0 / 92903.04
    mm_areas = [a * mm_factor for a in poly_areas_raw]
    if sum(1 for a in mm_areas if 10 < a < 5000) > len(realistic):
        return mm_factor
    return factor

def extract_room_dimension_pairs_from_text(raw_text: str) -> list[dict[str, Any]]:
    room_data = []
    text = raw_text.replace(" X ", "X")
    text = re.sub(r"\s+", " ", text)
    pattern = re.compile(
        r"(" + "|".join(re.escape(k) for k in ROOM_KEYWORDS_SORTED) + r")\s*([0-9]+(?:\.[0-9]+)?)\s*X\s*([0-9]+(?:\.[0-9]+)?)"
    )
    for match in pattern.finditer(text):
        room_name = canonicalize_room_label(match.group(1).strip())
        width, height = float(match.group(2)), float(match.group(3))
        raw_area = width * height
        if raw_area > 10000:
            area_sq_m = round(raw_area / 1_000_000, 2)
            unit = "mm"
        else:
            area_sq_m = round(raw_area, 2)
            unit = "m"
        area_sq_ft = round(area_sq_m * 10.7639, 2)
        room_data.append({
            "room": room_name, "width": width, "height": height,
            "area": area_sq_ft, "area_sq_m": area_sq_m,
            "unit": unit, "source": "dxf_dimension_text"
        })
    unique = {}
    for item in room_data:
        unique[(item["room"], item["width"], item["height"])] = item
    return list(unique.values())

def assign_floor_to_rooms(raw_text: str, rooms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rooms:
        return rooms
    ground_idx = raw_text.find("GROUND FLOOR")
    first_idx = raw_text.find("FIRST FLOOR")
    for room in rooms:
        room["floor"] = None
    if ground_idx != -1 and first_idx != -1:
        ground_chunk = raw_text[ground_idx:first_idx]
        first_chunk = raw_text[first_idx:]
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

# ─────────────────────────────────────────────
# Result builders
# ─────────────────────────────────────────────

def _build_result(
    source_type, method_used, room_types_found, room_instances_found,
    room_counts, features_found, room_data, total_area, raw_text,
    floors, area_statement, openings,
    layers=None, entity_counts=None, block_names=None,
    block_counts=None, closed_polyline_count=0, top_polyline_areas=None,
    note=None,
) -> dict[str, Any]:
    return {
        "source_type": source_type,
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
        "raw_text": raw_text,
        "layers": layers or [],
        "entity_counts": entity_counts or {},
        "block_names": block_names or [],
        "block_counts": block_counts or {},
        "closed_polyline_count": closed_polyline_count,
        "top_polyline_areas": top_polyline_areas or [],
        "floors": floors,
        "area_statement": area_statement,
        "openings": openings,
        "note": note,
    }

def _empty_result(source_type: str, note: str, **kwargs) -> dict[str, Any]:
    return _build_result(
        source_type=source_type, method_used=note,
        room_types_found=[], room_instances_found=[],
        room_counts={}, features_found=[], room_data=[],
        total_area=0.0, raw_text="", floors=[],
        area_statement={}, openings={"doors": [], "windows": []},
        note=kwargs.get("note", note),
    )

# ─────────────────────────────────────────────
# PDF Analysis
# ─────────────────────────────────────────────

def analyze_pdf(file_bytes: bytes) -> dict[str, Any]:
    # Try direct text extraction first
    pdf_text = clean_text(extract_pdf_text(file_bytes))

    if len(pdf_text) > 200:
        # Vector PDF — text extractable directly
        final_text = pdf_text
        method_used = "Direct PDF text extraction"
        room_types_found, room_instances_found, room_counts = build_room_response(final_text)
        features_found = find_keywords(final_text, FEATURE_KEYWORDS)
        room_data = []
        area_statement = extract_area_statement(final_text)
        openings = extract_opening_schedule(final_text)
        floors = extract_floors_from_text(final_text)
        total_area = infer_total_area_sq_ft(room_data, area_statement)
    elif TESSERACT_AVAILABLE:
        # Scanned/image PDF — convert to image and OCR
        method_used = "OCR with proximity spatial matching"
        try:
            images = convert_from_bytes(file_bytes, dpi=300)
        except Exception as e:
            return _empty_result("pdf", f"PDF to image conversion failed: {str(e)}")

        all_room_data = []
        all_raw_text_parts = []

        for img in images:
            try:
                ocr_data, raw_text = run_ocr_on_image(img)
                room_data_page = extract_rooms_from_ocr_data(ocr_data)
                all_room_data.extend(room_data_page)
                all_raw_text_parts.append(raw_text)
            except Exception as e:
                print(f"OCR failed on page: {e}", flush=True)

        final_text = " ".join(all_raw_text_parts)
        room_data = all_room_data
        room_types_found, room_instances_found, room_counts = build_room_response(final_text)
        if room_data:
            inferred_types, inferred_instances, inferred_counts = infer_room_instances_from_room_data(room_data)
            if len(inferred_instances) >= len(room_instances_found):
                room_types_found = inferred_types
                room_instances_found = inferred_instances
                room_counts = inferred_counts
        features_found = find_keywords(final_text, FEATURE_KEYWORDS)
        area_statement = extract_area_statement(final_text)
        openings = extract_opening_schedule(final_text)
        floors = extract_floors_from_text(final_text)
        total_area = infer_total_area_sq_ft(room_data, area_statement)
        print(f"PDF OCR: {len(room_data)} rooms, {total_area} sq ft", flush=True)
    else:
        # No OCR available — Vision only
        final_text = ""
        method_used = "Vision-only (Tesseract unavailable)"
        room_types_found, room_instances_found, room_counts = [], [], {}
        features_found, room_data = [], []
        area_statement = {}
        openings = {"doors": [], "windows": []}
        floors = []
        total_area = 0.0

    legacy_result = _build_result(
        "pdf", method_used, room_types_found, room_instances_found,
        room_counts, features_found, room_data, total_area,
        final_text, floors, area_statement, openings
    )

    if VISION_ENABLED and VISION_AVAILABLE:
        legacy_result["method_used"] = method_used + " + Gemini Vision"
        return analyze_pdf_with_vision(file_bytes, legacy_result)
    return legacy_result

# ─────────────────────────────────────────────
# Image Analysis
# ─────────────────────────────────────────────

def analyze_image(file_bytes: bytes) -> dict[str, Any]:
    try:
        image = Image.open(BytesIO(file_bytes)).convert("RGB")
    except Exception as e:
        return _empty_result("image", f"Failed to open image: {str(e)}")

    if TESSERACT_AVAILABLE:
        try:
            ocr_data, raw_text = run_ocr_on_image(image)
            room_data = extract_rooms_from_ocr_data(ocr_data)
            print(f"Image OCR: {len(room_data)} rooms detected", flush=True)
        except Exception as e:
            print(f"OCR failed: {e}", flush=True)
            raw_text, room_data = "", []
    else:
        print("Tesseract unavailable — Vision-only mode", flush=True)
        raw_text, room_data = "", []

    room_types_found, room_instances_found, room_counts = build_room_response(raw_text)
    if room_data:
        inferred_types, inferred_instances, inferred_counts = infer_room_instances_from_room_data(room_data)
        if len(inferred_instances) >= len(room_instances_found):
            room_types_found = inferred_types
            room_instances_found = inferred_instances
            room_counts = inferred_counts

    features_found = find_keywords(raw_text, FEATURE_KEYWORDS)
    area_statement = extract_area_statement(raw_text)
    openings = extract_opening_schedule(raw_text)
    floors = extract_floors_from_text(raw_text)
    total_area = infer_total_area_sq_ft(room_data, area_statement)

    legacy_result = _build_result(
        "image", "Proximity OCR spatial matching",
        room_types_found, room_instances_found, room_counts,
        features_found, room_data, total_area, raw_text,
        floors, area_statement, openings
    )

    if VISION_ENABLED and VISION_AVAILABLE:
        legacy_result["method_used"] = "Proximity OCR + Gemini Vision"
        return analyze_image_with_vision(file_bytes, legacy_result)
    return legacy_result

# ─────────────────────────────────────────────
# DXF Analysis
# ─────────────────────────────────────────────

def analyze_dxf(file_bytes: bytes) -> dict[str, Any]:
    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        doc = ezdxf.readfile(tmp_path)
        msp = doc.modelspace()
        sqft_factor = detect_dxf_unit_to_sqft_factor(doc)

        layers = [layer.dxf.name for layer in doc.layers]
        entity_counts: dict[str, int] = {}
        block_counts: dict[str, int] = {}
        extracted_texts: list[str] = []
        poly_areas_raw: list[float] = []
        closed_polyline_count = 0

        # Also collect text entity positions for spatial matching
        text_entities = []  # [(text, cx, cy)]

        for entity in msp:
            dtype = entity.dxftype()
            entity_counts[dtype] = entity_counts.get(dtype, 0) + 1
            txt = safe_entity_text(entity)
            if txt:
                extracted_texts.append(txt)
                try:
                    if dtype == "TEXT":
                        ins = entity.dxf.insert
                        text_entities.append((txt, float(ins.x), float(ins.y)))
                    elif dtype == "MTEXT":
                        ins = entity.dxf.insert
                        text_entities.append((txt, float(ins.x), float(ins.y)))
                except Exception:
                    pass
            if dtype == "INSERT":
                try:
                    block_name = str(entity.dxf.name)
                    block_counts[block_name] = block_counts.get(block_name, 0) + 1
                    insert_texts = extract_insert_texts(entity)
                    extracted_texts.extend(insert_texts)
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
                        poly_areas_raw.append(area)

        sqft_factor = validate_unit_factor(poly_areas_raw, sqft_factor)
        poly_areas = [round(a * sqft_factor, 2) for a in poly_areas_raw]

        raw_text = normalize_ocr_text(clean_text(" ".join(extracted_texts)))
        room_types_found, room_instances_found, room_counts = build_room_response(raw_text)
        features_found = find_keywords(raw_text, FEATURE_KEYWORDS)
        floors = extract_floors_from_text(raw_text)

        # Try dimension pairs first
        room_data = extract_room_dimension_pairs_from_text(raw_text)
        room_data = assign_floor_to_rooms(raw_text, room_data)

        # If no dimension pairs, try spatial text matching using polyline areas
        if not room_data and poly_areas and text_entities:
            room_data = _match_dxf_texts_to_polylines(
                text_entities, poly_areas_raw, sqft_factor, msp
            )

        area_statement = extract_area_statement(raw_text)
        openings = extract_opening_schedule(raw_text)
        total_area = infer_total_area_sq_ft(room_data, area_statement)

        # If still no area, use sum of polyline areas
        if total_area == 0 and poly_areas:
            realistic = [a for a in poly_areas if 10 < a < 5000]
            if realistic:
                total_area = round(sum(realistic), 2)

        block_names = sorted(block_counts.keys())
        top_polyline_areas = sorted(poly_areas, reverse=True)[:10]

        if room_data:
            inferred_types, inferred_instances, inferred_counts = infer_room_instances_from_room_data(room_data)
            if len(inferred_instances) >= len(room_instances_found):
                room_types_found = inferred_types
                room_instances_found = inferred_instances
                room_counts_out = inferred_counts
            else:
                room_counts_out = room_counts
        else:
            room_counts_out = room_counts

        legacy_dxf = _build_result(
            "dxf", "DXF CAD entity parsing + spatial matching",
            room_types_found, room_instances_found, room_counts_out,
            features_found, room_data, total_area, raw_text,
            floors, area_statement, openings,
            layers=layers, entity_counts=entity_counts,
            block_names=block_names, block_counts=block_counts,
            closed_polyline_count=closed_polyline_count,
            top_polyline_areas=top_polyline_areas
        )

        if VISION_ENABLED and VISION_AVAILABLE:
            legacy_dxf["method_used"] = "DXF parsing + Gemini Vision"
            return analyze_dxf_with_vision(file_bytes, legacy_dxf)
        return legacy_dxf

    except Exception as e:
        return _empty_result("dxf", f"DXF parsing failed: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def _match_dxf_texts_to_polylines(
    text_entities: list, poly_areas_raw: list[float],
    sqft_factor: float, msp
) -> list[dict[str, Any]]:
    """Match DXF text labels to enclosed polylines using point-in-polygon."""
    room_data = []
    # Get closed polylines with their geometry
    polylines = []
    for entity in msp:
        if entity.dxftype() in {"LWPOLYLINE", "POLYLINE"}:
            try:
                is_closed = bool(entity.closed)
            except Exception:
                is_closed = False
            if is_closed:
                pts = polyline_points(entity)
                if len(pts) >= 3:
                    area_raw = safe_polygon_area(pts)
                    area_sqft = round(area_raw * sqft_factor, 2)
                    if 10 < area_sqft < 5000:
                        try:
                            poly = Polygon(pts)
                            if poly.is_valid:
                                polylines.append({"poly": poly, "area": area_sqft})
                        except Exception:
                            pass

    for txt, cx, cy in text_entities:
        room_type = match_room_type_from_text(txt)
        if not room_type:
            continue
        pt = Point(cx, cy)
        for p in polylines:
            try:
                if p["poly"].contains(pt) or p["poly"].distance(pt) < 100:
                    room_data.append({
                        "room": room_type,
                        "label": normalize_ocr_text(txt),
                        "width": None, "height": None,
                        "area": p["area"],
                        "area_sq_m": round(p["area"] / 10.7639, 2),
                        "unit": "sq_ft",
                        "source": "dxf_point_in_polygon",
                        "floor": None,
                    })
                    break
            except Exception:
                pass

    return room_data

# ─────────────────────────────────────────────
# DWG Analysis
# ─────────────────────────────────────────────

def analyze_dwg(file_bytes: bytes) -> dict[str, Any]:
    print("Attempting DWG analysis...", flush=True)
    dxf_bytes = convert_dwg_to_dxf_bytes(file_bytes)
    if dxf_bytes:
        print("DWG → DXF conversion successful", flush=True)
        result = analyze_dxf(dxf_bytes)
        result["source_type"] = "dwg"
        result["method_used"] = "DWG→DXF + " + result.get("method_used", "DXF parsing")
        return result

    print("DWG conversion failed, falling back to Vision", flush=True)
    legacy_dwg = _empty_result("dwg", "DWG — Vision render")
    if VISION_ENABLED and VISION_AVAILABLE:
        return analyze_dwg_with_vision(file_bytes, legacy_dwg)
    legacy_dwg["note"] = (
        "DWG could not be converted. Try converting to DXF using AutoCAD, LibreCAD, "
        "or the free ODA File Converter (opendesign.com/guestfiles/oda_file_converter)."
    )
    return legacy_dwg

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

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
    return _empty_result("unknown", f"Unsupported file type: {filename}")