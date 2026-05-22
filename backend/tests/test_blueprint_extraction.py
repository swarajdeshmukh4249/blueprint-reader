"""Unit tests for blueprint extraction reliability."""

import unittest

from blueprint_logic import (
    compute_extraction_quality,
    dedupe_room_data,
    extract_rooms_from_plain_text,
    filter_sane_rooms,
    fix_ocr_text,
    get_dxf_area_scale,
    match_room,
    match_rooms_to_areas,
    normalize_text,
    parse_area,
    validate_unit_scale,
)


class TestTextExtraction(unittest.TestCase):
    def test_parse_area_sqft(self):
        self.assertEqual(parse_area("BEDROOM 120 SQ FT"), 120.0)
        self.assertEqual(parse_area("KITCHEN 45 SQFT"), 45.0)

    def test_parse_area_sqm(self):
        self.assertAlmostEqual(parse_area("ROOM 50 SQM"), 50 * 10.7639, places=1)

    def test_ocr_fixes(self):
        self.assertIn("BEDROOM", fix_ocr_text("8EDROOM 120 5Q FT"))

    def test_match_master_bedroom(self):
        self.assertEqual(match_room("MASTER BEDROOM"), "MASTER BEDROOM")
        self.assertEqual(match_room("MASTER BED ROOM"), "MASTER BEDROOM")

    def test_plain_text_multiline(self):
        text = "BEDROOM 120 SQ FT\nLIVING ROOM 200 SQ FT"
        rooms = extract_rooms_from_plain_text(text)
        names = {r["room"] for r in rooms}
        self.assertIn("BEDROOM", names)
        self.assertIn("LIVING ROOM", names)

    def test_dimension_pattern(self):
        text = "BEDROOM 12' x 10'"
        rooms = extract_rooms_from_plain_text(text)
        self.assertTrue(any(r["room"] == "BEDROOM" and r["area"] == 120 for r in rooms))

    def test_spatial_match(self):
        phrases = [
            {"text": "BEDROOM", "cx": 100, "cy": 100, "w": 80},
            {"text": "120 SQ FT", "cx": 110, "cy": 140, "w": 60},
        ]
        rooms = match_rooms_to_areas(phrases)
        self.assertEqual(len(rooms), 1)
        self.assertEqual(rooms[0]["area"], 120.0)

    def test_filter_sane_drops_huge(self):
        bad = [{"room": "BEDROOM", "area": 99999, "confidence": 0.9, "source": "ocr_inline"}]
        self.assertEqual(len(filter_sane_rooms(bad)), 0)

    def test_extraction_quality_high(self):
        result = {
            "room_data": [
                {"room": "BEDROOM", "area": 120, "confidence": 0.9, "source": "ocr_inline"},
                {"room": "KITCHEN", "area": 80, "confidence": 0.85, "source": "ocr_inline"},
            ],
            "total_area": 200,
        }
        q = compute_extraction_quality(result)
        self.assertGreaterEqual(q["score"], 0.75)
        self.assertEqual(q["level"], "high")


class TestDxfScale(unittest.TestCase):
    def test_validate_unit_scale_metric(self):
        polygons = [{"area": 12.0}, {"area": 15.0}, {"area": 10.0}]
        scale = validate_unit_scale(polygons, 1 / 144.0)
        self.assertAlmostEqual(scale, 10.7639, places=2)


if __name__ == "__main__":
    unittest.main()
