import { normalizeAnalysis } from '@/lib/normalizeAnalysis'
import type { AnalyzeBlueprintResponse } from '@/types/analysis'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function getAnalyzeUrl() {
  const raw = (import.meta.env.VITE_API_BASE_URL as string | undefined) || ''
  const base = raw.replace(/\/$/, '')

  // FastAPI mounts this at the app root: POST /analyze-blueprint
  // (not under /api/v1). Vite proxies `/analyze-blueprint` in dev.
  if (!base || base.startsWith('/')) {
    return '/analyze-blueprint'
  }

  try {
    const absolute = new URL(base)
    return `${absolute.origin}/analyze-blueprint`
  } catch {
    return '/analyze-blueprint'
  }
}

export async function analyzeBlueprint(file: File, token?: string): Promise<AnalyzeBlueprintResponse> {
  const url = getAnalyzeUrl()

  const form = new FormData()
  form.append('file', file)

  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let res: Response
  try {
    res = await fetch(url, {
      method: 'POST',
      body: form,
      headers,
    })
  } catch (error) {
    throw new ApiError(
      'Failed to reach the backend. Keep Terminal A running: python -m uvicorn main:app --reload --port 8000',
      0
    )
  }
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new ApiError(text || `Request failed (${res.status})`, res.status)
  }

  const json = (await res.json()) as unknown
  return normalizeAnalysis(json)
}

