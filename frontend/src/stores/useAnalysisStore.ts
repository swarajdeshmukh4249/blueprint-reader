import { create } from 'zustand'
import type { AnalyzeBlueprintResponse } from '@/types/analysis'

type Status = 'idle' | 'processing' | 'done' | 'error'

type AnalysisState = {
  status: Status
  filename?: string
  result?: AnalyzeBlueprintResponse
  errorMessage?: string
  setProcessing: (filename: string) => void
  setResult: (filename: string, result: AnalyzeBlueprintResponse) => void
  setError: (filename: string | undefined, message: string) => void
  reset: () => void
}

const STORAGE_KEY = 'blueprintReader:lastResult'

function safeParse(json: string | null): AnalyzeBlueprintResponse | undefined {
  if (!json) return undefined
  try {
    return JSON.parse(json) as AnalyzeBlueprintResponse
  } catch {
    return undefined
  }
}

const cached = safeParse(localStorage.getItem(STORAGE_KEY))

export const useAnalysisStore = create<AnalysisState>((set) => ({
  status: cached ? 'done' : 'idle',
  filename: undefined,
  result: cached,
  errorMessage: undefined,
  setProcessing: (filename) =>
    set({
      status: 'processing',
      filename,
      errorMessage: undefined,
    }),
  setResult: (filename, result) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(result))
    set({ status: 'done', filename, result, errorMessage: undefined })
  },
  setError: (filename, message) =>
    set({
      status: 'error',
      filename,
      errorMessage: message,
    }),
  reset: () => {
    localStorage.removeItem(STORAGE_KEY)
    set({ status: 'idle', filename: undefined, result: undefined, errorMessage: undefined })
  },
}))

