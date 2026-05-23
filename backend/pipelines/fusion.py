"""
Multi-source blueprint fusion (OCR + CAD geometry + Vision + geometry ML).

Patent-relevant: confidence-weighted merge of heterogeneous extractors.
"""

from __future__ import annotations
from typing import Any


def _area(r: dict) -> float:
    return float(r.get("area") or 0)


def merge_room_records(candidates: list[dict]) -> list[dict]:
    """Dedupe by room name; keep highest-confidence row with area."""
    by_room: dict[str, dict] = {}
    for row in candidates:
        name = (row.get("room") or "").upper().strip()
        if not name:
            continue
        prev = by_room.get(name)
        if not prev:
            by_room[name] = row
            continue
        if _area(row) > 0 and _area(prev) <= 0:
            by_room[name] = row
        elif float(row.get("confidence") or 0) > float(prev.get("confidence") or 0):
            by_room[name] = row
    return list(by_room.values())


def fuse_extraction_sources(sources: list[dict[str, Any]]) -> dict[str, Any]:
    """
    sources: list of partial results each with room_data, optional confidence, method tag.
    Returns fused room_data + fusion_metadata.
    """
    all_rooms: list[dict] = []
    methods: list[str] = []
    for src in sources:
        if not src:
            continue
        tag = src.get("source_tag") or src.get("method_used") or "unknown"
        methods.append(str(tag))
        for r in src.get("room_data") or []:
            row = dict(r)
            row["fusion_source"] = tag
            all_rooms.append(row)

    fused = merge_room_records(all_rooms)
    avg_conf = (
        sum(float(r.get("confidence") or 0) for r in fused) / len(fused) if fused else 0.0
    )
    return {
        "room_data": fused,
        "fusion_methods": methods,
        "fusion_confidence": round(avg_conf, 2),
        "fusion_room_count": len(fused),
    }
