"""
IFC (Industry Foundation Classes) import — Revit / ArchiCAD standard.
"""

from __future__ import annotations
import os
import tempfile
from typing import Any

try:
    import ifcopenshell
    import ifcopenshell.util.element as ifc_element
    IFC_AVAILABLE = True
except ImportError:
    IFC_AVAILABLE = False


def _space_area_sqm(space) -> float:
    try:
        for rel in space.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                props = rel.RelatingPropertyDefinition
                if props.is_a("IfcElementQuantity"):
                    for q in props.Quantities:
                        if q.is_a("IfcQuantityArea") and q.Name and "AREA" in q.Name.upper():
                            return float(q.AreaValue or 0)
    except Exception:
        pass
    return 0.0


def analyze_ifc(file_bytes: bytes) -> dict[str, Any]:
    if not IFC_AVAILABLE:
        return {
            "error": "IFC support not installed",
            "error_code": "IFC_UNAVAILABLE",
            "notes": "Install ifcopenshell on the worker: pip install ifcopenshell",
        }

    path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ifc") as tmp:
            tmp.write(file_bytes)
            path = tmp.name
        model = ifcopenshell.open(path)
        spaces = model.by_type("IfcSpace")
        room_data = []
        for sp in spaces:
            name = (getattr(sp, "LongName", None) or sp.Name or "SPACE").strip()
            area_m2 = _space_area_sqm(sp)
            if area_m2 <= 0:
                continue
            area_sqft = round(area_m2 * 10.7639, 2)
            room_data.append({
                "room": name.upper(),
                "label": name,
                "area": area_sqft,
                "unit": "sq ft",
                "width": None,
                "height": None,
                "confidence": 0.95,
                "source": "ifc_space",
            })

        walls = model.by_type("IfcWall")
        wall_meta = {
            "wall_count": len(walls),
            "external_count": sum(1 for w in walls if getattr(w, "IsExternal", False)),
            "internal_count": sum(1 for w in walls if not getattr(w, "IsExternal", False)),
        }

        total = sum(float(r.get("area") or 0) for r in room_data)
        return {
            "source_type": "ifc",
            "method_used": "IFC IfcSpace quantities (industry standard)",
            "unit_system": "sq ft",
            "room_data": room_data,
            "total_area": round(total, 2),
            "ifc_metadata": wall_meta,
            "notes": f"Parsed {len(room_data)} spaces from IFC.",
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "error_code": "IFC_PARSE_FAILED",
            "notes": "Could not read IFC file. Export IFC2x3 or IFC4 from your BIM tool.",
        }
    finally:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass
