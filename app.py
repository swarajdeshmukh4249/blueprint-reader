import pytesseract
from pdf2image import convert_from_bytes
from pypdf import PdfReader
from io import BytesIO
import re
import cv2
import numpy as np

ROOM_KEYWORDS = [
    "MASTER BEDROOM", "BED ROOM", "BEDROOM", "BEDROOM 1", "BEDROOM 2", "BEDROOM 3", "BEDRM",
    "KITCHEN", "HALL", "HALLWAY", "LIVING ROOM", "DINING", "DINING ROOM",
    "BATH", "BATHROOM", "BATHROOM 1", "BATHROOM 2", "TOILET", "WASH",
    "VERANDA", "SITTING ROOM", "STORAGE", "UTILITIES", "FRONT PORCH",
    "WALK-IN CLOSET", "CLOSET", "ENTRY"
]

FEATURE_KEYWORDS = [
    "GROUND FLOOR", "FIRST FLOOR", "SECOND FLOOR",
    "PASSAGE", "CAR PARKING", "STAIR", "BALCONY", "PORCH"
]


def clean_text(text):
    text = text.upper()
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_pdf_text(file_bytes):
    reader = PdfReader(BytesIO(file_bytes))
    full_text = []

    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            full_text.append(txt)

    return "\n".join(full_text)


def preprocess_image_for_ocr(pil_image):
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


def extract_ocr_text(file_bytes):
    images = convert_from_bytes(file_bytes, dpi=300)
    ocr_text = []

    for image in images:
        processed = preprocess_image_for_ocr(image)

        text = pytesseract.image_to_string(
            processed,
            config="--psm 6"
        )

        ocr_text.append(text)

    return "\n".join(ocr_text)


def find_keywords(text, keywords):
    found = []

    for keyword in keywords:
        if keyword in text:
            found.append(keyword)

    return sorted(list(set(found)))


def is_valid_room_name(room_name):
    return any(keyword in room_name for keyword in ROOM_KEYWORDS)


def normalize_room_name(room_name):
    room_name = re.sub(r"\s+", " ", room_name.strip())
    return room_name


def extract_room_data(text):

    results = []

    normalized_text = text.upper()
    normalized_text = re.sub(r"\s+", " ", normalized_text)

    # ROOM 12 x 10 pattern
    dim_pattern = r"([A-Z0-9 ]{3,40}?)\s+(\d+(?:\.\d+)?)\s*[\'\"]?\s*[Xx]\s*(\d+(?:\.\d+)?)\s*[\'\"]?"

    dim_matches = re.findall(dim_pattern, normalized_text)

    for match in dim_matches:
        room_name = normalize_room_name(match[0])
        width = float(match[1])
        height = float(match[2])

        if is_valid_room_name(room_name):

            results.append({
                "room": room_name,
                "width": width,
                "height": height,
                "area": round(width * height, 2),
                "unit": "ft",
                "source": "dimensions"
            })

    # ROOM 85 SQ FT pattern
    area_pattern = r"([A-Z0-9 ]{3,50}?)\s+(\d+(?:\.\d+)?)\s*SQ\.?\s*F\s*T"

    area_matches = re.findall(area_pattern, normalized_text)

    for match in area_matches:

        room_name = normalize_room_name(match[0])
        area = float(match[1])

        if is_valid_room_name(room_name):

            results.append({
                "room": room_name,
                "width": None,
                "height": None,
                "area": round(area, 2),
                "unit": "sq ft",
                "source": "sq_ft_label"
            })

    unique_results = []
    seen = set()

    for item in results:

        key = (item["room"], item["area"], item["source"])

        if key not in seen:
            seen.add(key)
            unique_results.append(item)

    return unique_results


def calculate_total_area(room_data):

    total_area = 0

    for item in room_data:
        total_area += item["area"]

    return round(total_area, 2)


def estimate_materials(total_area):

    bricks = total_area * 8
    cement_bags = total_area * 0.4
    steel_kg = total_area * 4
    tiles_area = total_area * 1.05

    materials = {
        "Bricks": int(bricks),
        "Cement Bags": int(cement_bags),
        "Steel (kg)": int(steel_kg),
        "Floor Tiles (sq ft)": int(tiles_area)
    }

    return materials


def estimate_costs(total_area):

    base_construction_rate = 1800
    flooring_rate = 120
    paint_rate = 80
    electrical_plumbing_rate = 250

    base_construction_cost = total_area * base_construction_rate
    flooring_cost = total_area * flooring_rate
    paint_cost = total_area * paint_rate
    electrical_plumbing_cost = total_area * electrical_plumbing_rate

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
        "Total Estimated Cost": round(total_estimated_cost, 2)
    }


def analyze_blueprint(file_bytes):

    pdf_text = clean_text(extract_pdf_text(file_bytes))

    if len(pdf_text) > 20:
        final_text = pdf_text
        method_used = "Direct PDF text extraction"
    else:
        final_text = clean_text(extract_ocr_text(file_bytes))
        method_used = "OCR fallback with preprocessing"

    rooms_found = find_keywords(final_text, ROOM_KEYWORDS)
    features_found = find_keywords(final_text, FEATURE_KEYWORDS)

    room_data = extract_room_data(final_text)

    total_area = calculate_total_area(room_data)

    materials = estimate_materials(total_area)

    costs = estimate_costs(total_area)

    return {
        "method": method_used,
        "rooms": rooms_found,
        "features": features_found,
        "room_data": room_data,
        "total_area": total_area,
        "materials": materials,
        "costs": costs,
        "raw_text": final_text
    }