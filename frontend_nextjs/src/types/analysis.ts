export type AnalyzeBlueprintRoom = {
  name?: string
  area?: number
  unit?: string
  confidence?: number
  notes?: string
}

export type AnalyzeBlueprintTotals = {
  total_area?: number
  unit?: string
  room_count?: number
}

export type AnalyzeBlueprintBoqItem = {
  item?: string
  quantity?: number
  unit?: string
  rate?: number
  amount?: number
}

export type AnalyzeBlueprintResponse = {
  rooms?: AnalyzeBlueprintRoom[]
  totals?: AnalyzeBlueprintTotals
  boq?: AnalyzeBlueprintBoqItem[]
  raw?: unknown
}

