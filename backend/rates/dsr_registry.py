"""
DSR rate schedule registry — Maharashtra, Delhi, and generic state PWD placeholders.
"""

from __future__ import annotations
from typing import Any

# Base rates per sqm / unit — extend with official DSR PDF imports per state
SCHEDULES: dict[str, dict[str, Any]] = {
    "maharashtra_pwd_2023_24": {
        "label": "Maharashtra PWD DSR 2023-24",
        "currency": "INR",
        "gst_pct": 18.0,
        "labour_pct_of_subtotal": 0.35,
        "rates": {
            "brickwork_sqm_230mm": 2850,
            "brickwork_sqm_115mm": 1650,
            "plaster_sqm": 420,
            "flooring_sqm": 850,
            "painting_sqm": 95,
            "rcc_slab_sqm": 5200,
            "steel_kg": 68,
            "cement_bag": 410,
        },
    },
    "delhi_dsr_2024": {
        "label": "Delhi Schedule of Rates (DSR) 2024 — indicative",
        "currency": "INR",
        "gst_pct": 18.0,
        "labour_pct_of_subtotal": 0.38,
        "rates": {
            "brickwork_sqm_230mm": 3020,
            "brickwork_sqm_115mm": 1780,
            "plaster_sqm": 445,
            "flooring_sqm": 920,
            "painting_sqm": 102,
            "rcc_slab_sqm": 5450,
            "steel_kg": 72,
            "cement_bag": 425,
        },
    },
    "generic_india_pwd": {
        "label": "Generic India PWD (national average)",
        "currency": "INR",
        "gst_pct": 18.0,
        "labour_pct_of_subtotal": 0.36,
        "rates": {
            "brickwork_sqm_230mm": 2900,
            "brickwork_sqm_115mm": 1700,
            "plaster_sqm": 430,
            "flooring_sqm": 880,
            "painting_sqm": 98,
            "rcc_slab_sqm": 5300,
            "steel_kg": 70,
            "cement_bag": 415,
        },
    },
}


def get_schedule(schedule_id: str | None = None) -> dict[str, Any]:
    sid = schedule_id or "maharashtra_pwd_2023_24"
    return SCHEDULES.get(sid) or SCHEDULES["maharashtra_pwd_2023_24"]


def list_schedules() -> list[dict[str, str]]:
    return [{"id": k, "label": v["label"]} for k, v in SCHEDULES.items()]
