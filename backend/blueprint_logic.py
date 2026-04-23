# UPDATED BLUEPRINT LOGIC (FIXED AREA + DXF ACCURACY + FALLBACKS)

import os
import re
import tempfile
from io import BytesIO
from typing import Any, Optional

import ezdxf
from shapely.geometry import Polygon

print("NEW BLUEPRINT LOGIC RUNNING")

# ---------------------------
# CORE FIX: AREA FROM DXF
# ---------------------------

def extract_area_from_polylines(msp):
    areas = []
    polyline_count = 0

    for entity in msp.query("LWPOLYLINE"):
        polyline_count += 1
        try:
            if entity.closed:
                points = [(p[0], p[1]) for p in entity]
                if len(points) >= 3:
                    poly = Polygon(points)
                    if poly.is_valid and poly.area > 10:
                        areas.append(poly.area)
        except Exception:
            continue

    print("Total polylines found:", polyline_count)
    print("Valid polygons used:", len(areas))

    if not areas:
        return 0.0

    # take largest polygon
    raw_area = max(areas)

    # -------- FIX: UNIT SCALING --------
    # Many DXF files are in mm → convert to sq ft
    # Heuristic: if area is too large, assume mm²
    if raw_area > 1_000_000:  # likely mm²
        # mm² → ft² conversion
        scaled_area = raw_area / 92903
    elif raw_area > 10_000:  # could be cm²
        scaled_area = raw_area / 929
    else:
        # already likely in ft²
        scaled_area = raw_area

    return round(scaled_area, 2)


# ---------------------------
# TEXT AREA EXTRACTION
# ---------------------------

def extract_area_from_text(text: str) -> float:
    text = text.upper()

    patterns = [
        r"TOTAL.*?([0-9]+)\s*SQ\s*FT",
        r"BUILT.*?([0-9]+)\s*SQ\s*FT",
        r"AREA.*?([0-9]+)\s*SQ\s*FT",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))

    return 0.0


# ---------------------------
# MATERIAL + COST
# ---------------------------

def estimate_materials(area):
    return {
        "Bricks": int(area * 8),
        "Cement Bags": int(area * 0.4),
        "Steel (kg)": int(area * 4),
    }


def estimate_cost(area):
    return int(area * 1800)


# ---------------------------
# MAIN DXF ANALYSIS (FIXED)
# ---------------------------

def analyze_dxf(file_bytes: bytes):
    tmp_path = ""

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        doc = ezdxf.readfile(tmp_path)
        msp = doc.modelspace()

        # 1. AREA FROM GEOMETRY (PRIMARY)
        poly_area = extract_area_from_polylines(msp)

        # 2. TEXT EXTRACTION (FALLBACK)
        texts = []
        for e in msp:
            try:
                if e.dxftype() == "TEXT":
                    texts.append(e.dxf.text)
                elif e.dxftype() == "MTEXT":
                    texts.append(e.text)
            except:
                pass

        raw_text = " ".join(texts)
        text_area = extract_area_from_text(raw_text)

        # 3. FINAL AREA DECISION (IMPORTANT FIX)
        # smarter decision: prefer text if it's significantly larger (common in plans)
        if text_area > poly_area * 1.2:
            final_area = text_area
        else:
            final_area = poly_area

        return {
            "source_type": "dxf",
            "method_used": "Improved DXF parsing",
            "polyline_area": poly_area,
            "text_area": text_area,
            "total_area": final_area,
            "debug_polyline_area": poly_area,
            "debug_text_area": text_area,
            "materials": estimate_materials(final_area),
            "cost": estimate_cost(final_area),
            "raw_text": raw_text,
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ---------------------------
# ENTRY POINT
# ---------------------------

def analyze_blueprint(file_bytes: bytes, filename: str):
    if filename.lower().endswith(".dxf"):
        return analyze_dxf(file_bytes)

    return {
        "error": "Only DXF supported in this optimized version"
    }