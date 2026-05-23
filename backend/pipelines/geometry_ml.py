"""
Geometry-based room / opening detection (rule-based CV; hook for trained models later).

Industry path: replace detect_rooms_from_contours() with YOLO / Mask R-CNN weights.
"""

from __future__ import annotations
from typing import Any, Optional

import numpy as np

try:
    import cv2
    CV2 = True
except ImportError:
    CV2 = False


def detect_rooms_from_image(image, scale_sqft_per_px2: float = 0.0) -> list[dict]:
    """Contour-based room candidates from rasterized plan."""
    if not CV2 or image is None:
        return []

    if hasattr(image, "mode"):
        img = np.array(image.convert("L"))
    else:
        img = image

    blur = cv2.GaussianBlur(img, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((3, 3), np.uint8)
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = img.shape[:2]
    min_area_px = (min(h, w) * 0.02) ** 2
    max_area_px = h * w * 0.4
    rooms = []

    for cnt in contours:
        area_px = cv2.contourArea(cnt)
        if area_px < min_area_px or area_px > max_area_px:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        area_sqft = round(area_px * scale_sqft_per_px2, 2) if scale_sqft_per_px2 > 0 else 0
        rooms.append({
            "room": "SPACE",
            "label": f"geom_{x}_{y}",
            "area": area_sqft,
            "unit": "sq ft",
            "width": None,
            "height": None,
            "confidence": 0.55,
            "source": "geometry_ml_contour",
            "bbox": [int(x), int(y), int(bw), int(bh)],
        })
    return rooms


def detect_openings_from_geometry(walls_data: dict, room_data: list[dict]) -> dict[str, Any]:
    """Heuristic door/window counts until symbol detector is trained."""
    room_count = len(room_data)
    toilets = sum(1 for r in room_data if "TOILET" in (r.get("room") or "") or "BATH" in (r.get("room") or ""))
    bedrooms = sum(1 for r in room_data if "BED" in (r.get("room") or ""))
    return {
        "doors": [
            {"room": "MAIN", "count": 1, "type": "main"},
            {"room": "BEDROOM", "count": max(bedrooms, 1), "type": "bedroom"},
            {"room": "TOILET", "count": max(toilets, 1), "type": "toilet"},
        ],
        "windows": [
            {"room": "GENERAL", "count": max(room_count, 2), "type": "sliding"},
        ],
    }
