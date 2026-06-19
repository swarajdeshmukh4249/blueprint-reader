import pytesseract
from pdf2image import convert_from_bytes
from pypdf import PdfReader
from io import BytesIO
import re
import cv2
import numpy as np
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

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
    
    logger.info(f"PDF has {len(reader.pages)} pages")

    for page_num, page in enumerate(reader.pages):
        txt = page.extract_text()
        if txt:
            logger.info(f"Page {page_num + 1} extracted text length: {len(txt)} characters")
            logger.info(f"Page {page_num + 1} text preview: {txt[:200]}")
            full_text.append(txt)
        else:
            logger.warning(f"Page {page_num + 1} returned no text")

    result = "\n".join(full_text)
    logger.info(f"Total PDF text length: {len(result)} characters")
    return result


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
    # Increase DPI for better resolution on vector/CAD-style PDFs
    dpi = 400  # Increased from 300 for better text extraction
    logger.info(f"Starting OCR text extraction with DPI={dpi}")
    images = convert_from_bytes(file_bytes, dpi=dpi)
    logger.info(f"Converted PDF to {len(images)} images at DPI={dpi}")
    
    ocr_text = []

    for idx, image in enumerate(images):
        logger.info(f"Processing image {idx + 1}/{len(images)}, size: {image.size}")
        processed = preprocess_image_for_ocr(image)

        text = pytesseract.image_to_string(
            processed,
            config="--psm 6"
        )
        
        logger.info(f"Image {idx + 1} OCR text length: {len(text)} characters")
        logger.info(f"Image {idx + 1} OCR text preview: {text[:300]}")
        ocr_text.append(text)

    result = "\n".join(ocr_text)
    logger.info(f"Total OCR text length: {len(result)} characters")
    return result


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

    logger.info(f"Normalized text length: {len(normalized_text)} characters")
    logger.info(f"Normalized text preview: {normalized_text[:500]}")

    # ROOM 12 x 10 pattern
    dim_pattern = r"([A-Z0-9 ]{3,40}?)\s+(\d+(?:\.\d+)?)\s*[\'\"]?\s*[Xx]\s*(\d+(?:\.\d+)?)\s*[\'\"]?"

    dim_matches = re.findall(dim_pattern, normalized_text)
    logger.info(f"Found {len(dim_matches)} dimension pattern matches")

    for match in dim_matches:
        room_name = normalize_room_name(match[0])
        width = float(match[1])
        height = float(match[2])

        logger.info(f"Dimension match: room='{room_name}', width={width}, height={height}")

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
    logger.info(f"Found {len(area_matches)} area pattern matches")

    for match in area_matches:

        room_name = normalize_room_name(match[0])
        area = float(match[1])

        logger.info(f"Area match: room='{room_name}', area={area}")

        if is_valid_room_name(room_name):

            results.append({
                "room": room_name,
                "width": None,
                "height": None,
                "area": round(area, 2),
                "unit": "sq ft",
                "source": "sq_ft_label"
            })

    logger.info(f"Total room entries before deduplication: {len(results)}")
    
    # Fix: Remove area from deduplication key to prevent merging rooms with same name but different areas
    unique_results = []
    seen = set()

    for item in results:
        # Use only room name and source for deduplication, not area
        key = (item["room"], item["source"])

        if key not in seen:
            seen.add(key)
            unique_results.append(item)
        else:
            logger.warning(f"Duplicate room detected and skipped: {item['room']} (source: {item['source']})")

    logger.info(f"Total room entries after deduplication: {len(unique_results)}")
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

    logger.info("Starting blueprint analysis")
    pdf_text = clean_text(extract_pdf_text(file_bytes))

    if len(pdf_text) > 20:
        final_text = pdf_text
        method_used = "Direct PDF text extraction"
        logger.info("Using direct PDF text extraction")
    else:
        final_text = clean_text(extract_ocr_text(file_bytes))
        method_used = "OCR fallback with preprocessing"
        logger.info("Using OCR fallback with preprocessing")

    rooms_found = find_keywords(final_text, ROOM_KEYWORDS)
    features_found = find_keywords(final_text, FEATURE_KEYWORDS)
    
    logger.info(f"Rooms found: {rooms_found}")
    logger.info(f"Features found: {features_found}")

    room_data = extract_room_data(final_text)

    total_area = calculate_total_area(room_data)
    logger.info(f"Total calculated area: {total_area} sq ft")
    
    # Sanity check: if total area is suspiciously low, flag as low confidence
    MIN_REASONABLE_AREA = 50  # Minimum reasonable total area in sq ft
    if total_area < MIN_REASONABLE_AREA and len(room_data) > 0:
        logger.warning(f"LOW CONFIDENCE: Total area {total_area} sq ft is below minimum threshold of {MIN_REASONABLE_AREA} sq ft")
        logger.warning(f"Detected {len(room_data)} rooms but total area is implausibly low")
        # Add warning to result
        low_confidence_warning = f"Low confidence: Total area ({total_area} sq ft) is below minimum threshold. Scale calibration may be incorrect."

    materials = estimate_materials(total_area)

    costs = estimate_costs(total_area)

    result = {
        "method": method_used,
        "rooms": rooms_found,
        "features": features_found,
        "room_data": room_data,
        "total_area": total_area,
        "materials": materials,
        "costs": costs,
        "raw_text": final_text
    }
    
    # Add low confidence warning if applicable
    if total_area < MIN_REASONABLE_AREA and len(room_data) > 0:
        result["warning"] = low_confidence_warning
        result["confidence"] = "low"
    
    logger.info("Blueprint analysis completed")
    return result