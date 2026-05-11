"""
boq_engine.py
─────────────
Full Bill of Quantities engine based on Maharashtra PWD DSR 2023-24 rates.

Covers:
  Substructure  — excavation, PCC, RCC footings
  Superstructure — brickwork, RCC columns/beams/slabs
  Finishes       — plastering, flooring (room-type specific), painting
  Openings       — doors, windows, ventilators
  Services       — plumbing, electrical, drainage
  External works — boundary wall, compound, water tank
  Extras         — waterproofing, false ceiling, miscellaneous

All rates are Maharashtra PWD DSR 2023-24 (Pune division).
Quantities are derived from building geometry extracted from the blueprint.

Usage:
    from boq_engine import generate_boq
    result = generate_boq(analysis_result)
    # result = { "items": [...], "summary": {...}, "grand_total": float }
"""

from __future__ import annotations
from typing import Any

# ─────────────────────────────────────────────────────────────────
# Maharashtra PWD DSR 2023-24 rates (₹)
# Source: Maharashtra PWD DSR Pune Division 2023-24
# ─────────────────────────────────────────────────────────────────

RATES = {
    # Earthwork & Substructure
    "excavation_cum":           65.00,    # per cum — manual excavation
    "pcc_cum":                  4800.00,  # per cum — M10 PCC
    "rcc_footing_cum":          9200.00,  # per cum — M20 RCC footing
    "footing_formwork_sqm":     280.00,   # per sqm — shuttering

    # Superstructure — RCC
    "rcc_column_cum":           10500.00, # per cum — M20 columns
    "rcc_beam_slab_cum":        9800.00,  # per cum — M20 beams+slab
    "rcc_formwork_sqm":         320.00,   # per sqm — shuttering

    # Brickwork
    "brickwork_sqm_230mm":      2400.00,  # per sqm — 230mm external wall
    "brickwork_sqm_115mm":      1400.00,  # per sqm — 115mm internal wall
    "brick_unit":               9.50,     # per brick — standard modular

    # Cement & Steel (market rate Pune 2024)
    "cement_bag_50kg":          420.00,   # per bag
    "steel_kg":                 72.00,    # per kg — Fe500 TMT

    # Plastering
    "plaster_external_sqm":     220.00,   # per sqm — 20mm CM 1:4
    "plaster_internal_sqm":     165.00,   # per sqm — 12mm CM 1:6
    "ceiling_plaster_sqm":      185.00,   # per sqm

    # Flooring — by room type (per sqft)
    "floor_marble_sqft":        280.00,   # living room, dining, master bedroom
    "floor_vitrified_sqft":     145.00,   # bedrooms, hall
    "floor_ceramic_sqft":       95.00,    # kitchen, utility
    "floor_antiskid_sqft":      110.00,   # bathroom, toilet
    "floor_parking_sqft":       65.00,    # parking — PCC + hardener
    "floor_terrace_sqft":       85.00,    # terrace — IPS finish

    # Dado (wall tiles)
    "dado_bathroom_sqft":       130.00,   # full height
    "dado_kitchen_sqft":        110.00,   # 2ft above counter

    # Doors & Windows
    "door_main_unit":           18000.00, # main door — teak frame + panel
    "door_bedroom_unit":        9500.00,  # bedroom — sal wood
    "door_toilet_unit":         6500.00,  # toilet — WPC/flush
    "window_sliding_sqft":      850.00,   # UPVC sliding
    "window_casement_sqft":     950.00,   # UPVC casement
    "ventilator_unit":          2200.00,  # louvre ventilator

    # Painting
    "paint_exterior_sqft":      55.00,    # 2 coats exterior emulsion
    "paint_interior_sqft":      38.00,    # 2 coats interior emulsion
    "paint_ceiling_sqft":       32.00,    # ceiling — white distemper

    # Plumbing (per sqft of built-up area)
    "plumbing_rate_sqft":       185.00,   # complete CP fittings + pipes
    "sanitary_per_toilet":      22000.00, # EWC, wash basin, shower, fittings
    "water_tank_litre":         6.50,     # overhead HDPE tank

    # Electrical (per sqft)
    "electrical_rate_sqft":     155.00,   # wiring, switches, DB, MCB
    "electrical_ac_point":      3500.00,  # per AC point
    "electrical_light_point":   1200.00,  # per light/fan point

    # Waterproofing
    "waterproofing_terrace_sqft":   95.00,  # terrace — 4 coat system
    "waterproofing_bathroom_sqft":  85.00,  # bathroom — crystalline
    "waterproofing_basement_sqft":  120.00, # basement — membrane

    # False ceiling
    "false_ceiling_gypsum_sqft":    145.00, # gypsum board false ceiling
    "false_ceiling_pop_sqft":       95.00,  # POP false ceiling

    # External works
    "boundary_wall_rmt":        2800.00,  # per rmt — 1.5m height brickwork
    "gate_main_unit":           35000.00, # MS fabricated main gate
    "compound_flooring_sqft":   45.00,    # paver blocks
    "garden_sqft":              35.00,    # topsoil + grass

    # Miscellaneous
    "staircase_rmt":            8500.00,  # per rmt — RCC stair with railing
    "lift_unit":                850000.00,# 6-person lift (4-5 floor building)
    "septic_tank_unit":         45000.00, # standard 2000L septic tank
}

# ─────────────────────────────────────────────────────────────────
# Room type classification
# ─────────────────────────────────────────────────────────────────

ROOM_CATEGORIES = {
    "premium": ["MASTER BEDROOM", "LIVING ROOM", "DRAWING ROOM", "LOUNGE", "LOBBY", "RECEPTION", "CONFERENCE"],
    "standard": ["BEDROOM", "BED ROOM", "HALL", "DINING", "DINING ROOM", "STUDY", "OFFICE", "CABIN"],
    "utility": ["KITCHEN", "UTILITY", "STORE", "STORAGE", "PANTRY", "DRY AREA", "BALCONY"],
    "wet": ["BATHROOM", "TOILET", "WC", "WASH ROOM", "WASHROOM", "BATH", "POWDER ROOM"],
    "parking": ["PARKING", "CAR PORCH", "CAR PARK", "GARAGE", "STILT"],
    "service": ["STAIR", "STAIRCASE", "LIFT", "CORRIDOR", "PASSAGE", "LOBBY", "FOYER"],
    "external": ["TERRACE", "TERRACE GARDEN", "HEAD ROOM", "MUMTY"],
}

def classify_room(room_name: str) -> str:
    name = room_name.upper().strip()
    for category, keywords in ROOM_CATEGORIES.items():
        if any(kw in name for kw in keywords):
            return category
    return "standard"


# ─────────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────────

def sqft_to_sqm(sqft: float) -> float:
    return round(sqft / 10.7639, 3)

def sqft_to_cum(sqft: float, thickness_m: float) -> float:
    """Convert sq ft area to cubic meters given thickness in meters."""
    return round(sqft_to_sqm(sqft) * thickness_m, 3)

def wall_area_sqm(perimeter_m: float, height_m: float = 3.0, openings_sqm: float = 0.0) -> float:
    """Net wall area after deducting openings."""
    return round(max(0, perimeter_m * height_m - openings_sqm), 2)


# ─────────────────────────────────────────────────────────────────
# BOQ line item builder
# ─────────────────────────────────────────────────────────────────

def item(
    sno: str,
    description: str,
    unit: str,
    qty: float,
    rate: float,
    category: str,
    notes: str = "",
) -> dict:
    amount = round(qty * rate, 2)
    return {
        "sno": sno,
        "description": description,
        "unit": unit,
        "qty": round(qty, 2),
        "rate": rate,
        "amount": amount,
        "category": category,
        "notes": notes,
    }


# ─────────────────────────────────────────────────────────────────
# Main BOQ generator
# ─────────────────────────────────────────────────────────────────

def generate_boq(analysis: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a full itemised BOQ from blueprint analysis output.

    Parameters
    ----------
    analysis : dict
        Output from analyze_blueprint() — contains room_data, total_area,
        features_found, openings, floor_count, drawing_type, etc.

    Returns
    -------
    dict with keys:
        items      — list of BOQ line items
        summary    — totals by category
        grand_total — ₹ total
        area_statement — key areas used for calculation
        rates_basis — "Maharashtra PWD DSR 2023-24"
    """
    items: list[dict] = []
    sno = [0]

    def add(description, unit, qty, rate, category, notes=""):
        if qty <= 0:
            return
        sno[0] += 1
        items.append(item(
            str(sno[0]), description, unit, qty, rate, category, notes
        ))

    # ── Extract key values from analysis ───────────────────────────────────
    total_area    = float(analysis.get("total_area") or 0)
    room_data     = analysis.get("room_data") or []
    features      = [f.upper() for f in (analysis.get("features_found") or [])]
    openings      = analysis.get("openings") or {}
    floor_count   = int(analysis.get("floor_count") or 1)
    building_type = _infer_building_type(analysis)

    if total_area <= 0:
        return {"items": [], "summary": {}, "grand_total": 0,
                "error": "Total area could not be determined from blueprint"}

    total_area_sqm = sqft_to_sqm(total_area)

    # Estimate plot/footprint area
    footprint_sqft = total_area / max(floor_count, 1)
    footprint_sqm  = sqft_to_sqm(footprint_sqft)

    # Estimate perimeter (assume roughly square footprint)
    import math
    perimeter_m = round(4 * math.sqrt(footprint_sqm), 2)

    # Count rooms by category
    room_areas: dict[str, float] = {}
    for rd in room_data:
        cat  = classify_room(rd.get("room", ""))
        area = float(rd.get("area") or 0)
        room_areas[cat] = room_areas.get(cat, 0) + area

    wet_area    = room_areas.get("wet", 0)
    parking_area = room_areas.get("parking", 0)
    terrace_area = room_areas.get("external", 0)
    interior_area = total_area - parking_area - terrace_area

    # Count toilets/bathrooms
    toilet_count = sum(1 for rd in room_data if classify_room(rd.get("room","")) == "wet")
    toilet_count = max(toilet_count, 1)

    # Count doors and windows from openings data
    all_doors   = openings.get("doors", [])
    all_windows = openings.get("windows", [])
    main_doors  = sum(d.get("count", 1) for d in all_doors if "main" in d.get("type","").lower())
    toilet_doors = sum(d.get("count", 1) for d in all_doors if "toilet" in d.get("type","").lower())
    bedroom_doors = sum(d.get("count", 1) for d in all_doors if "bedroom" in d.get("type","").lower())
    other_doors  = sum(d.get("count", 1) for d in all_doors) - main_doors - toilet_doors - bedroom_doors
    total_windows = sum(w.get("count", 1) for w in all_windows)

    # If no door/window data, estimate from room count
    room_count = len(room_data) or 1
    if not all_doors:
        main_doors    = 1
        toilet_doors  = toilet_count
        bedroom_doors = max(1, room_count - toilet_count - 2)
        other_doors   = 1
    if not all_windows:
        total_windows = max(4, room_count * 2)

    # Wall area estimate
    avg_floor_height_m = 3.0
    ext_wall_area_sqm  = wall_area_sqm(perimeter_m, avg_floor_height_m * floor_count, openings_sqm=total_windows * 1.5)
    int_wall_area_sqm  = wall_area_sqm(perimeter_m * 1.5, avg_floor_height_m * floor_count, openings_sqm=len(all_doors) * 2.0)

    # ── SECTION A: SUBSTRUCTURE ─────────────────────────────────────────────
    excav_vol  = sqft_to_cum(footprint_sqft * 1.3, 1.5)   # 1.5m deep, 30% extra for working space
    pcc_vol    = sqft_to_cum(footprint_sqft * 1.1, 0.075) # 75mm PCC bed
    footing_vol = sqft_to_cum(footprint_sqft * 0.15, 0.6) # RCC footings

    add("Excavation for foundation including disposal", "Cum", excav_vol, RATES["excavation_cum"], "A. Substructure")
    add("Plain Cement Concrete M10 in foundation bed", "Cum", pcc_vol, RATES["pcc_cum"], "A. Substructure")
    add("RCC M20 for isolated/combined footings", "Cum", footing_vol, RATES["rcc_footing_cum"], "A. Substructure")
    add("Shuttering for footing formwork", "Sqm", footing_vol * 4, RATES["footing_formwork_sqm"], "A. Substructure")

    # ── SECTION B: RCC FRAMEWORK ────────────────────────────────────────────
    col_vol  = round(total_area_sqm * 0.025 * floor_count, 2)  # ~2.5% of floor area per floor
    slab_vol = sqft_to_cum(total_area, 0.125)                   # 125mm slab thickness

    add("RCC M20 for columns including reinforcement & formwork", "Cum", col_vol, RATES["rcc_column_cum"], "B. RCC Framework",
        "Fe500 steel @ 120 kg/cum included in rate")
    add("RCC M20 for beams & slabs including reinforcement & formwork", "Cum", slab_vol, RATES["rcc_beam_slab_cum"], "B. RCC Framework",
        "Fe500 steel @ 150 kg/cum included in rate")

    # Separate steel BOQ for client reference
    total_steel_kg = round((col_vol * 120) + (slab_vol * 150), 0)
    add("Structural steel Fe500 TMT (indicative — included in RCC rates above)", "Kg",
        total_steel_kg, 0, "B. RCC Framework", "For reference only — cost included in RCC items")

    # Cement BOQ
    total_cement_bags = round((excav_vol * 0) + (pcc_vol * 4) + (footing_vol * 6.5) + (slab_vol * 7), 0)
    add("Cement OPC 53 grade (indicative)", "Bags", total_cement_bags, 0, "B. RCC Framework",
        "For reference only — included in respective item rates")

    # ── SECTION C: BRICKWORK ─────────────────────────────────────────────────
    add("230mm thick brickwork in CM 1:5 for external walls", "Sqm",
        ext_wall_area_sqm, RATES["brickwork_sqm_230mm"], "C. Brickwork",
        "Modular bricks, first class")
    add("115mm thick brickwork in CM 1:6 for internal partition walls", "Sqm",
        int_wall_area_sqm * 0.6, RATES["brickwork_sqm_115mm"], "C. Brickwork")

    # Brick count for reference
    total_bricks = int((ext_wall_area_sqm * 60) + (int_wall_area_sqm * 0.6 * 55))
    add("Modular bricks 230x115x75mm (indicative)", "Nos", total_bricks, 0, "C. Brickwork",
        "For reference only — included in brickwork rates")

    # ── SECTION D: PLASTERING ────────────────────────────────────────────────
    add("20mm external cement plaster CM 1:4 including sponge finish", "Sqm",
        ext_wall_area_sqm, RATES["plaster_external_sqm"], "D. Plastering")
    add("12mm internal cement plaster CM 1:6 including smooth finish", "Sqm",
        int_wall_area_sqm, RATES["plaster_internal_sqm"], "D. Plastering")
    add("Ceiling plaster 6mm CM 1:4", "Sqm",
        total_area_sqm, RATES["ceiling_plaster_sqm"], "D. Plastering")

    # ── SECTION E: FLOORING ──────────────────────────────────────────────────
    # Room-type specific flooring
    premium_area = room_areas.get("premium", 0)
    standard_area = room_areas.get("standard", 0)
    utility_area  = room_areas.get("utility", 0)

    # If Gemini didn't break down room areas, estimate from total
    if premium_area + standard_area + utility_area < total_area * 0.3:
        premium_area  = total_area * 0.25
        standard_area = total_area * 0.35
        utility_area  = total_area * 0.15

    if premium_area > 0:
        add("Italian Marble / Granite flooring for Living, Dining & Master Bedroom", "Sqft",
            premium_area, RATES["floor_marble_sqft"], "E. Flooring",
            "18mm thick, machine polished")
    if standard_area > 0:
        add("Vitrified tile flooring 600x600mm for Bedrooms & Hall", "Sqft",
            standard_area, RATES["floor_vitrified_sqft"], "E. Flooring",
            "Double charged vitrified tiles")
    if utility_area > 0:
        add("Ceramic tile flooring 300x300mm for Kitchen & Utility", "Sqft",
            utility_area, RATES["floor_ceramic_sqft"], "E. Flooring")
    if wet_area > 0:
        add("Anti-skid ceramic tile flooring for Bathrooms & Toilets", "Sqft",
            wet_area, RATES["floor_antiskid_sqft"], "E. Flooring",
            "300x300mm anti-skid")
    if parking_area > 0:
        add("PCC flooring with hardener for Parking / Car Porch", "Sqft",
            parking_area, RATES["floor_parking_sqft"], "E. Flooring")
    if terrace_area > 0:
        add("IPS flooring with slope for Terrace", "Sqft",
            terrace_area, RATES["floor_terrace_sqft"], "E. Flooring",
            "50mm IPS with water proofing compound")

    # Dado (wall tiles)
    if wet_area > 0:
        add("Ceramic dado tiles for Bathrooms — full height 7ft", "Sqft",
            wet_area * 3.5, RATES["dado_bathroom_sqft"], "E. Flooring",
            "300x450mm glazed ceramic tiles")
        add("Kitchen dado tiles above counter — 2ft height", "Sqft",
            utility_area * 0.5, RATES["dado_kitchen_sqft"], "E. Flooring")

    # ── SECTION F: DOORS & WINDOWS ───────────────────────────────────────────
    if main_doors > 0:
        add("Main entrance door — Teak wood frame with decorative panel", "Nos",
            main_doors, RATES["door_main_unit"], "F. Doors & Windows",
            "100x75mm frame, 38mm thick flush door with teak veneer")
    if bedroom_doors > 0:
        add("Bedroom doors — Sal wood frame with flush door shutter", "Nos",
            bedroom_doors, RATES["door_bedroom_unit"], "F. Doors & Windows",
            "100x65mm frame, 35mm flush door")
    if toilet_doors > 0:
        add("Toilet / Bathroom doors — WPC frame with WPC shutter", "Nos",
            toilet_doors, RATES["door_toilet_unit"], "F. Doors & Windows",
            "Waterproof WPC — moisture resistant")
    if other_doors > 0:
        add("Other doors — Sal wood frame with flush door shutter", "Nos",
            other_doors, RATES["door_bedroom_unit"], "F. Doors & Windows")
    if total_windows > 0:
        avg_window_sqft = 12.0  # standard 3x4ft window
        add("UPVC sliding windows with glass — 3 track", "Sqft",
            total_windows * avg_window_sqft, RATES["window_sliding_sqft"], "F. Doors & Windows",
            "5mm clear float glass, white UPVC sections")
        add("Ventilators — louvre type aluminium", "Nos",
            max(toilet_count, 2), RATES["ventilator_unit"], "F. Doors & Windows")

    # ── SECTION G: PAINTING ──────────────────────────────────────────────────
    add("Exterior wall painting — 2 coats weather shield emulsion", "Sqft",
        ext_wall_area_sqm * 10.7639, RATES["paint_exterior_sqft"], "G. Painting",
        "Asian Paints Apex / equivalent, after primer")
    add("Interior wall painting — 2 coats interior emulsion", "Sqft",
        int_wall_area_sqm * 10.7639, RATES["paint_interior_sqft"], "G. Painting",
        "Asian Paints Tractor / equivalent, after putty & primer")
    add("Ceiling painting — white distemper / OBD", "Sqft",
        total_area, RATES["paint_ceiling_sqft"], "G. Painting")

    # ── SECTION H: PLUMBING & SANITARY ───────────────────────────────────────
    add("Complete internal plumbing — CPVC pipes, CP fittings, valves", "Sqft",
        interior_area, RATES["plumbing_rate_sqft"], "H. Plumbing & Sanitary",
        "Hot & cold water supply, waste water drainage")
    add("Sanitary fixtures per toilet — EWC, wash basin, shower, CP fittings", "Nos",
        toilet_count, RATES["sanitary_per_toilet"], "H. Plumbing & Sanitary",
        "Parryware / Hindware or equivalent")

    # Water tank
    water_tank_litres = max(1000, total_area * 0.8)  # ~0.8L per sqft
    add("HDPE overhead water storage tank", "Litres",
        water_tank_litres, RATES["water_tank_litre"], "H. Plumbing & Sanitary",
        "ISI marked, UV stabilised")

    # Septic tank if no municipal sewage
    has_septic = any("SEPTIC" in f for f in features)
    if has_septic or floor_count <= 2:
        add("Brick masonry septic tank with inlet/outlet arrangements", "Nos",
            1, RATES["septic_tank_unit"], "H. Plumbing & Sanitary",
            "Designed for occupancy based on floor count")

    # ── SECTION I: ELECTRICAL ────────────────────────────────────────────────
    add("Complete electrical wiring — FR cables, modular switches, DB, MCB", "Sqft",
        interior_area, RATES["electrical_rate_sqft"], "I. Electrical",
        "Finolex / Havells wires, Anchor/Legrand switches")
    add("Light & fan points including wiring & accessories", "Nos",
        room_count * 3, RATES["electrical_light_point"], "I. Electrical")
    add("AC points including wiring, isolator & copper pipe provision", "Nos",
        max(2, room_count - toilet_count), RATES["electrical_ac_point"], "I. Electrical")

    # ── SECTION J: WATERPROOFING ─────────────────────────────────────────────
    if terrace_area > 0:
        add("Terrace waterproofing — 4-coat crystalline + IPS finishing", "Sqft",
            terrace_area, RATES["waterproofing_terrace_sqft"], "J. Waterproofing",
            "Roff / Dr. Fixit crystalline waterproofing")
    if wet_area > 0:
        add("Bathroom & toilet waterproofing — crystalline treatment", "Sqft",
            wet_area, RATES["waterproofing_bathroom_sqft"], "J. Waterproofing",
            "300mm upstand on walls, 2 coats")

    # ── SECTION K: FALSE CEILING ─────────────────────────────────────────────
    false_ceiling_area = premium_area + standard_area * 0.5
    if false_ceiling_area > 0:
        add("Gypsum board false ceiling for Living, Dining & Master Bedroom", "Sqft",
            false_ceiling_area * 0.6, RATES["false_ceiling_gypsum_sqft"], "K. False Ceiling",
            "12.5mm gypsum board on MS framework, including cove")
        add("POP false ceiling for other rooms", "Sqft",
            false_ceiling_area * 0.4, RATES["false_ceiling_pop_sqft"], "K. False Ceiling")

    # ── SECTION L: EXTERNAL WORKS ─────────────────────────────────────────────
    has_boundary = any("BOUNDARY" in f or "COMPOUND" in f for f in features)
    boundary_rmt = perimeter_m * 1.2  # slightly larger than building perimeter

    add("Boundary wall — brick masonry 230mm x 1.5m height with plaster & coping", "Rmt",
        boundary_rmt, RATES["boundary_wall_rmt"], "L. External Works",
        "Including MS grille on top")
    add("Main gate — MS fabricated with enamel paint", "Nos",
        1, RATES["gate_main_unit"], "L. External Works",
        "Double leaf, 12ft wide x 6ft height")
    add("Compound flooring — interlocking paver blocks 60mm", "Sqft",
        footprint_sqft * 0.4, RATES["compound_flooring_sqft"], "L. External Works",
        "Grey / red paver blocks")

    # Staircase
    has_stair = any("STAIR" in f for f in features) or floor_count > 1
    if has_stair:
        stair_rmt = floor_count * 3.2  # ~3.2m per floor
        add("RCC staircase with MS/SS railing and nosing", "Rmt",
            stair_rmt, RATES["staircase_rmt"], "L. External Works",
            "Including anti-skid nosing tiles")

    # Lift — for buildings > 4 floors
    if floor_count >= 4 or any("LIFT" in f for f in features):
        add("Passenger lift — 6 person capacity, automatic doors", "Nos",
            1, RATES["lift_unit"], "L. External Works",
            "Including civil shaft, machine room, AMC for 1 year")

    # ── SECTION M: CONTINGENCIES & SUPERVISION ────────────────────────────────
    subtotal = sum(i["amount"] for i in items if i["amount"] > 0)
    contingency = round(subtotal * 0.05, 2)
    supervision  = round(subtotal * 0.03, 2)

    sno[0] += 1
    items.append({
        "sno": str(sno[0]),
        "description": "Contingencies @ 5% of subtotal",
        "unit": "LS", "qty": 1, "rate": contingency, "amount": contingency,
        "category": "M. Contingencies", "notes": "Unforeseen items"
    })
    sno[0] += 1
    items.append({
        "sno": str(sno[0]),
        "description": "Site supervision & project management @ 3%",
        "unit": "LS", "qty": 1, "rate": supervision, "amount": supervision,
        "category": "M. Contingencies", "notes": ""
    })

    # ── Summary ───────────────────────────────────────────────────────────────
    categories: dict[str, float] = {}
    for it in items:
        cat = it["category"]
        categories[cat] = round(categories.get(cat, 0) + it["amount"], 2)

    grand_total = round(sum(it["amount"] for it in items), 2)
    cost_per_sqft = round(grand_total / total_area, 2) if total_area > 0 else 0

    return {
        "items": items,
        "summary": categories,
        "grand_total": grand_total,
        "cost_per_sqft": cost_per_sqft,
        "rates_basis": "Maharashtra PWD DSR 2023-24 (Pune Division)",
        "area_statement": {
            "total_area_sqft": total_area,
            "total_area_sqm": total_area_sqm,
            "footprint_sqft": footprint_sqft,
            "floor_count": floor_count,
            "toilet_count": toilet_count,
            "room_count": room_count,
        },
        "building_type": building_type,
    }


def _infer_building_type(analysis: dict) -> str:
    features = [f.upper() for f in (analysis.get("features_found") or [])]
    rooms = [r.get("room", "").upper() for r in (analysis.get("room_data") or [])]
    all_text = " ".join(features + rooms)

    if any(k in all_text for k in ["OFFICE", "CONFERENCE", "RECEPTION", "CABIN", "SHOWROOM"]):
        return "Commercial"
    if any(k in all_text for k in ["SHOP", "RETAIL", "MALL", "WAREHOUSE"]):
        return "Industrial/Retail"
    if any(k in all_text for k in ["HOTEL", "HOSTEL", "DORMITORY"]):
        return "Hospitality"
    return "Residential"