"""
Wall thickness and type from DXF layers and parallel line pairs.
"""

from __future__ import annotations
from typing import Any

import ezdxf
from shapely.geometry import LineString


EXTERNAL_LAYER_HINTS = ("WALL", "EXT", "EXTERIOR", "OUTER", "FACADE", "BOUNDARY")
INTERNAL_LAYER_HINTS = ("PARTITION", "INT", "INTERNAL", "INNER", "CHB")


def _layer_name(entity) -> str:
    try:
        return (entity.dxf.layer or "").upper()
    except Exception:
        return ""


def _line_segments(msp) -> list[dict]:
    segs = []
    for entity in msp:
        try:
            if entity.dxftype() == "LINE":
                x1, y1 = float(entity.dxf.start.x), float(entity.dxf.start.y)
                x2, y2 = float(entity.dxf.end.x), float(entity.dxf.end.y)
                layer = _layer_name(entity)
                length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                if length < 50:
                    continue
                segs.append({"layer": layer, "length": length, "line": LineString([(x1, y1), (x2, y2)])})
            elif entity.dxftype() == "LWPOLYLINE":
                pts = [(float(p[0]), float(p[1])) for p in entity.get_points("xy")]
                layer = _layer_name(entity)
                for i in range(len(pts) - 1):
                    x1, y1 = pts[i]
                    x2, y2 = pts[i + 1]
                    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                    if length < 50:
                        continue
                    segs.append({"layer": layer, "length": length, "line": LineString([(x1, y1), (x2, y2)])})
        except Exception:
            continue
    return segs


def _parallel_distance(line_a, line_b) -> float:
    try:
        return line_a.line.distance(line_b.line)
    except Exception:
        return 1e9


def detect_walls_from_dxf(doc) -> dict[str, Any]:
    msp = doc.modelspace()
    segs = _line_segments(msp)
    if not segs:
        return {"walls": [], "external_area_sqft": 0, "internal_area_sqft": 0}

    thickness_samples: list[float] = []
    external_len = 0.0
    internal_len = 0.0

    for i, a in enumerate(segs):
        layer = a["layer"]
        if any(h in layer for h in EXTERNAL_LAYER_HINTS):
            external_len += a["length"]
        elif any(h in layer for h in INTERNAL_LAYER_HINTS):
            internal_len += a["length"]
        for j in range(i + 1, min(i + 40, len(segs))):
            b = segs[j]
            d = _parallel_distance(a, b)
            if 50 < d < 600:
                thickness_samples.append(d)

    thickness_samples.sort()
    median_thick = thickness_samples[len(thickness_samples) // 2] if thickness_samples else 230.0

    ext_mm = 230 if median_thick > 150 else 115
    int_mm = 115 if median_thick > 150 else 75

    walls = [
        {
            "type": "external",
            "thickness_mm": ext_mm,
            "total_length_draw": round(external_len, 2),
            "rate_key": "brickwork_sqm_230mm",
        },
        {
            "type": "internal",
            "thickness_mm": int_mm,
            "total_length_draw": round(internal_len, 2),
            "rate_key": "brickwork_sqm_115mm",
        },
    ]
    return {
        "walls": walls,
        "median_wall_thickness_draw": round(median_thick, 2),
        "external_length_draw": round(external_len, 2),
        "internal_length_draw": round(internal_len, 2),
        "method": "dxf_layers_and_parallel_lines",
    }
