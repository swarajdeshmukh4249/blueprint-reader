"""
Orchestrates scale, walls, geometry ML, and multi-source fusion after base extraction.
"""

from __future__ import annotations
from typing import Any, Optional

from pipelines.fusion import fuse_extraction_sources
from pipelines.scale_detection import parse_scale_from_text, apply_scale_to_areas
from pipelines.wall_detection import detect_walls_from_dxf
from pipelines.geometry_ml import detect_openings_from_geometry

try:
    from pipelines.geometry_ml import detect_rooms_from_image
except ImportError:
    detect_rooms_from_image = None  # type: ignore


def enhance_analysis(
    result: dict[str, Any],
    *,
    dxf_doc=None,
    raster_image=None,
    linear_scale: float = 1.0,
) -> dict[str, Any]:
    """Enrich analysis dict in-place with industry pipeline outputs."""
    if result.get("error"):
        return result

    raw = result.get("raw_text") or ""
    sources = [{"room_data": result.get("room_data") or [], "source_tag": result.get("method_used")}]

    scale_info = parse_scale_from_text(raw)
    if scale_info:
        result["scale_detection"] = scale_info
        rooms, new_scale = apply_scale_to_areas(
            result.get("room_data") or [],
            scale_info,
            linear_scale,
        )
        if new_scale != linear_scale:
            result["room_data"] = rooms
            result["total_area"] = round(sum(float(r.get("area") or 0) for r in rooms), 2)

    if dxf_doc is not None:
        wall_data = detect_walls_from_dxf(dxf_doc)
        result["walls"] = wall_data
        result["wall_thickness"] = {
            "external_mm": wall_data["walls"][0]["thickness_mm"] if wall_data.get("walls") else 230,
            "internal_mm": wall_data["walls"][1]["thickness_mm"] if len(wall_data.get("walls") or []) > 1 else 115,
            "method": wall_data.get("method"),
        }

    if raster_image is not None and detect_rooms_from_image:
        geom_rooms = detect_rooms_from_image(raster_image)
        if geom_rooms:
            sources.append({"room_data": geom_rooms, "source_tag": "geometry_ml_contour"})

    if len(sources) > 1:
        fused = fuse_extraction_sources(sources)
        result["room_data"] = fused["room_data"]
        result["fusion"] = {
            "methods": fused["fusion_methods"],
            "confidence": fused["fusion_confidence"],
            "room_count": fused["fusion_room_count"],
        }
        result["method_used"] = (result.get("method_used") or "") + " + multi-source fusion"

    openings = detect_openings_from_geometry(result.get("walls") or {}, result.get("room_data") or [])
    result["openings"] = openings

    return result
