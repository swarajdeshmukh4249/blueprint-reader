import { normalizeAnalysis } from '@/lib/normalizeAnalysis'
import type { AnalyzeBlueprintResponse } from '@/types/analysis'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function getApiBaseUrl() {
  const raw = import.meta.env.VITE_API_BASE_URL as string | undefined
  // Same-origin in dev (Vite proxies /analyze-blueprint); production can set full URL.
  return (raw ?? '').replace(/\/$/, '')
}

export async function analyzeBlueprint(file: File, token?: string): Promise<AnalyzeBlueprintResponse> {
  const baseUrl = getApiBaseUrl()
  const url = `${baseUrl}/analyze-blueprint`

  const form = new FormData()
  form.append('file', file)

  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(url, { 
    method: 'POST', 
    body: form,
    headers
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new ApiError(text || `Request failed (${res.status})`, res.status)
  }

  const json = (await res.json()) as unknown
  return normalizeAnalysis(json)
}

