"""
Scale bar and drawing-scale detection from CAD text and raster OCR blobs.
"""

from __future__ import annotations

import re
from typing import Any, Optional

# Drawing units → real-world mm per drawing unit when scale is 1:ratio
SCALE_TEXT = re.compile(
    r"(?:SCALE|SC\.?)\s*[:=]?\s*1\s*[:/]\s*(\d+)",
    re.IGNORECASE,
)
RATIO_INLINE = re.compile(r"1\s*[:/]\s*(\d{1,4})\s*(?:@|AT)?", re.IGNORECASE)
GRAPHIC_BAR = re.compile(
    r"(\d+)\s*(?:M|METRE|Meter|FT|FEET|')\s*(?:=|\-|TO)\s*(\d+(?:\.\d+)?)\s*(?:MM|CM|M|FT|')?",
    re.IGNORECASE,
)


def parse_scale_from_text(text: str) -> Optional[dict[str, Any]]:
    if not text:
        return None
    blob = text.upper()
    m = SCALE_TEXT.search(blob) or RATIO_INLINE.search(blob)
    if m:
        ratio = int(m.group(1))
        if 1 <= ratio <= 5000:
            return {
                "scale_ratio": f"1:{ratio}",
                "scale_factor": ratio,
                "method": "text_scale_notation",
                "confidence": 0.9,
            }
    gm = GRAPHIC_BAR.search(blob)
    if gm:
        return {
            "scale_ratio": "graphic_bar",
            "real_value": gm.group(1),
            "draw_value": gm.group(2),
            "method": "graphic_scale_bar",
            "confidence": 0.75,
        }
    return None


def apply_scale_to_areas(
    room_data: list[dict],
    scale_info: dict[str, Any],
    current_unit_scale: float,
) -> tuple[list[dict], float]:
    """
    When text says 1:100 and areas were computed in wrong units, adjust multiplier.
    Returns updated rooms + combined linear scale factor.
    """
    factor = float(scale_info.get("scale_factor") or 0)
    if factor <= 1:
        return room_data, current_unit_scale

    # If drawing is unitless at 1:100, areas scale by factor^2
    area_mult = (factor ** 2) if scale_info.get("method") == "text_scale_notation" else 1.0
    if area_mult == 1.0:
        return room_data, current_unit_scale

    out = []
    for r in room_data:
        nr = dict(r)
        if nr.get("area"):
            nr["area"] = round(float(nr["area"]) * area_mult, 2)
            nr["scale_adjusted"] = True
        out.append(nr)
    return out, current_unit_scale * area_mult
