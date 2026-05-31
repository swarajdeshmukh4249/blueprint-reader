import type {
  AnalyzeBlueprintBoqItem,
  AnalyzeBlueprintResponse,
  AnalyzeBlueprintRoom,
  AnalyzeBlueprintTotals,
} from '@/types/analysis'

function toNumber(value: unknown): number | undefined {
  if (typeof value === 'number') return Number.isFinite(value) ? value : undefined
  if (typeof value === 'string') {
    const n = parseFloat(value)
    return Number.isFinite(n) ? n : undefined
  }
  return undefined
}

function asString(value: unknown): string | undefined {
  return typeof value === 'string' && value.trim() ? value : undefined
}

function asRecords(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value)
    ? value.filter(
        (v): v is Record<string, unknown> => typeof v === 'object' && v !== null,
      )
    : []
}

/**
 * Adapts the FastAPI `/analyze-blueprint` payload (`room_data`, `total_area`,
 * `boq_items`, `unit_system`, …) onto the shape the UI renders (`rooms`,
 * `totals`, `boq`). If the backend already returns the UI shape those keys win.
 * The original payload is preserved on `raw` so the raw JSON view stays intact.
 */
export function normalizeAnalysis(payload: unknown): AnalyzeBlueprintResponse {
  if (typeof payload !== 'object' || payload === null) {
    return { raw: payload }
  }

  const raw = payload as Record<string, unknown>
  const unit = asString(raw.unit_system) ?? 'sq ft'

  const existingRooms = asRecords(raw.rooms)
  const roomSource = existingRooms.length ? existingRooms : asRecords(raw.room_data)
  const rooms: AnalyzeBlueprintRoom[] = roomSource.map((r) => {
    const name = asString(r.name) ?? asString(r.room) ?? asString(r.label)
    const label = asString(r.label)
    return {
      name,
      area: toNumber(r.area),
      unit: asString(r.unit) ?? unit,
      confidence: toNumber(r.confidence),
      notes: asString(r.notes) ?? (label && label !== name ? label : undefined),
    }
  })

  const existingTotals =
    typeof raw.totals === 'object' && raw.totals !== null
      ? (raw.totals as Record<string, unknown>)
      : {}
  const totals: AnalyzeBlueprintTotals = {
    total_area: toNumber(existingTotals.total_area) ?? toNumber(raw.total_area),
    unit: asString(existingTotals.unit) ?? unit,
    room_count: toNumber(existingTotals.room_count) ?? rooms.length,
    boq_total:
      toNumber(raw.boq_total) ??
      toNumber((raw.gst_breakdown as Record<string, unknown> | undefined)?.grand_total_with_gst),
    cost_per_sqft: toNumber(raw.cost_per_sqft),
  }

  const existingBoq = asRecords(raw.boq)
  const boqSource = existingBoq.length ? existingBoq : asRecords(raw.boq_items)
  const boq: AnalyzeBlueprintBoqItem[] = boqSource.map((b) => ({
    item: asString(b.item) ?? asString(b.description),
    quantity: toNumber(b.quantity) ?? toNumber(b.qty),
    unit: asString(b.unit),
    rate: toNumber(b.rate),
    amount: toNumber(b.amount),
    category: asString(b.category),
  }))

  return { rooms, totals, boq, raw }
}
