import { describe, expect, it } from 'vitest'
import { normalizeAnalysis } from '@/lib/normalizeAnalysis'

// Mirrors the real FastAPI /analyze-blueprint payload (see backend/blueprint_logic.py).
const backendPayload = {
  source_type: 'dxf',
  method_used: 'DXF geometry + label proximity (scale=1)',
  unit_system: 'sq ft',
  total_area: 3900,
  cost_per_sqft: 2230,
  boq_total: 8697000,
  room_data: [
    {
      room: 'MASTER BEDROOM',
      label: 'MASTER BEDROOM-1 13 2 X10',
      area: 1950,
      unit: 'sq ft',
      confidence: 0.9,
      source: 'dxf_text_spatial',
    },
    {
      room: 'BEDROOM',
      label: 'GENERAL BEDROOM 14 8 X10',
      area: 1950,
      unit: 'sq ft',
      confidence: 0.9,
      source: 'dxf_text_spatial',
    },
  ],
  boq_items: [
    {
      sno: '1',
      description: 'Brick masonry in CM 1:6',
      unit: 'cum',
      qty: 42,
      rate: 6500,
      amount: 273000,
      category: 'Civil',
    },
  ],
  gst_breakdown: { grand_total_with_gst: 8697000 },
}

describe('normalizeAnalysis', () => {
  it('maps room_data → rooms with name/area/unit/confidence', () => {
    const result = normalizeAnalysis(backendPayload)
    expect(result.rooms).toHaveLength(2)
    expect(result.rooms?.[0]).toMatchObject({
      name: 'MASTER BEDROOM',
      area: 1950,
      unit: 'sq ft',
      confidence: 0.9,
    })
    // label carried into notes when it differs from the room name
    expect(result.rooms?.[0].notes).toBe('MASTER BEDROOM-1 13 2 X10')
  })

  it('maps top-level total_area/unit_system → totals', () => {
    const result = normalizeAnalysis(backendPayload)
    expect(result.totals).toMatchObject({
      total_area: 3900,
      unit: 'sq ft',
      room_count: 2,
      boq_total: 8697000,
      cost_per_sqft: 2230,
    })
  })

  it('maps boq_items → boq with item/quantity/amount', () => {
    const result = normalizeAnalysis(backendPayload)
    expect(result.boq).toHaveLength(1)
    expect(result.boq?.[0]).toMatchObject({
      item: 'Brick masonry in CM 1:6',
      quantity: 42,
      unit: 'cum',
      rate: 6500,
      amount: 273000,
    })
  })

  it('preserves the original payload on raw', () => {
    const result = normalizeAnalysis(backendPayload)
    expect(result.raw).toBe(backendPayload)
  })

  it('falls back to boq_total from gst_breakdown when absent at top level', () => {
    const { boq_total, ...rest } = backendPayload
    void boq_total
    const result = normalizeAnalysis(rest)
    expect(result.totals?.boq_total).toBe(8697000)
  })

  it('respects the UI shape when the backend already returns rooms/totals/boq', () => {
    const result = normalizeAnalysis({
      rooms: [{ name: 'KITCHEN', area: 120 }],
      totals: { total_area: 120, unit: 'sq ft', room_count: 1 },
      boq: [{ item: 'Tiles', amount: 5000 }],
    })
    expect(result.rooms?.[0]).toMatchObject({ name: 'KITCHEN', area: 120 })
    expect(result.totals?.total_area).toBe(120)
    expect(result.boq?.[0]).toMatchObject({ item: 'Tiles', amount: 5000 })
  })

  it('handles non-object payloads gracefully', () => {
    const result = normalizeAnalysis('boom')
    expect(result.raw).toBe('boom')
    expect(result.rooms).toBeUndefined()
  })
})
