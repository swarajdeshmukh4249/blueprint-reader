import { Copy, Download, RotateCcw } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import Container from '@/components/Container'
import { cn } from '@/lib/utils'
import { useAnalysisStore } from '@/stores/useAnalysisStore'
import type { AnalyzeBlueprintRoom } from '@/types/analysis'

function toCsv(rooms: AnalyzeBlueprintRoom[]) {
  const header = ['name', 'area', 'unit', 'confidence', 'notes']
  const lines = [
    header.join(','),
    ...rooms.map((r) =>
      [
        r.name ?? '',
        r.area ?? '',
        r.unit ?? '',
        r.confidence ?? '',
        (r.notes ?? '').split('"').join('""'),
      ]
        .map((v) => `"${String(v)}"`)
        .join(','),
    ),
  ]
  return lines.join('\n')
}

function formatInr(value?: number) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value)
}

function download(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function Results() {
  const filename = useAnalysisStore((s) => s.filename)
  const result = useAnalysisStore((s) => s.result)
  const reset = useAnalysisStore((s) => s.reset)

  if (!result) {
    return (
      <Container className="pt-12 pb-16">
        <div className="rounded-3xl border border-ink/10 bg-paper/60 p-10 text-center shadow-soft">
          <div className="font-display text-3xl tracking-tight">No results yet</div>
          <div className="mt-3 text-sm text-ink/70">
            Upload a blueprint to generate a room schedule and export-ready data.
          </div>
          <NavLink
            to="/upload"
            className="mt-6 inline-flex rounded-full bg-ink px-5 py-3 text-sm font-medium text-paper transition hover:-translate-y-px hover:bg-ink/90"
          >
            Go to Upload
          </NavLink>
        </div>
      </Container>
    )
  }

  const rooms = Array.isArray(result.rooms) ? result.rooms : []
  const boq = Array.isArray(result.boq) ? result.boq : []
  const totals = result.totals
  const roomCount = totals?.room_count ?? rooms.length
  const pretty = JSON.stringify(result.raw ?? result, null, 2)

  return (
    <div className="pb-16">
      <Container className="pt-10 md:pt-14">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="space-y-2">
            <div className="text-xs tracking-[0.22em] text-ink/55">RESULTS</div>
            <h1 className="font-display text-4xl leading-[0.95] tracking-tight md:text-5xl">
              Takeoff output
            </h1>
            <div className="text-sm text-ink/70">
              {filename ? <span className="font-medium text-ink">{filename}</span> : 'Latest analysis'}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => {
                navigator.clipboard.writeText(pretty)
              }}
              className="inline-flex items-center gap-2 rounded-full border border-ink/12 bg-paper/60 px-4 py-2 text-sm text-ink/80 transition hover:bg-paper hover:text-ink"
            >
              <Copy className="h-4 w-4" />
              Copy JSON
            </button>
            <button
              type="button"
              onClick={() => download('blueprint-result.json', pretty, 'application/json')}
              className="inline-flex items-center gap-2 rounded-full border border-ink/12 bg-paper/60 px-4 py-2 text-sm text-ink/80 transition hover:bg-paper hover:text-ink"
            >
              <Download className="h-4 w-4" />
              Download JSON
            </button>
            {rooms.length > 0 && (
              <button
                type="button"
                onClick={() => download('blueprint-rooms.csv', toCsv(rooms), 'text/csv')}
                className="inline-flex items-center gap-2 rounded-full border border-ink/12 bg-paper/60 px-4 py-2 text-sm text-ink/80 transition hover:bg-paper hover:text-ink"
              >
                <Download className="h-4 w-4" />
                Download CSV
              </button>
            )}
            <button
              type="button"
              onClick={reset}
              className="inline-flex items-center gap-2 rounded-full border border-ink/12 bg-paper/60 px-4 py-2 text-sm text-ink/80 transition hover:bg-paper hover:text-ink"
            >
              <RotateCcw className="h-4 w-4" />
              Reset
            </button>
          </div>
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-12">
          <div className="md:col-span-4">
            <div className="rounded-3xl border border-ink/10 bg-paper/60 p-6 shadow-soft">
              <div className="text-xs tracking-[0.2em] text-ink/55">SUMMARY</div>
              <div className="mt-4 space-y-4">
                <div className="rounded-2xl border border-ink/10 bg-paper/50 p-4">
                  <div className="text-xs text-ink/60">Rooms</div>
                  <div className="mt-2 font-display text-3xl tracking-tight">
                    {roomCount}
                  </div>
                </div>
                <div className="rounded-2xl border border-ink/10 bg-paper/50 p-4">
                  <div className="text-xs text-ink/60">Total Area</div>
                  <div className="mt-2 font-display text-3xl tracking-tight">
                    {totals?.total_area ?? '—'}{' '}
                    <span className="text-base text-ink/60">{totals?.unit ?? ''}</span>
                  </div>
                </div>
                {typeof totals?.boq_total === 'number' && totals.boq_total > 0 && (
                  <div className="rounded-2xl border border-ink/10 bg-paper/50 p-4">
                    <div className="text-xs text-ink/60">BOQ Total</div>
                    <div className="mt-2 font-display text-3xl tracking-tight">
                      {formatInr(totals.boq_total)}
                    </div>
                    {typeof totals?.cost_per_sqft === 'number' && totals.cost_per_sqft > 0 && (
                      <div className="mt-1 text-xs text-ink/60">
                        {formatInr(totals.cost_per_sqft)} / sq ft
                      </div>
                    )}
                  </div>
                )}
                <NavLink
                  to="/upload"
                  className="inline-flex w-full items-center justify-center rounded-full bg-ink px-5 py-3 text-sm font-medium text-paper transition hover:-translate-y-px hover:bg-ink/90"
                >
                  Analyze another file
                </NavLink>
              </div>
            </div>
          </div>

          <div className="md:col-span-8">
            <div className="rounded-3xl border border-ink/10 bg-paper/60 p-6 shadow-soft">
              <div className="flex items-center justify-between">
                <div className="text-xs tracking-[0.2em] text-ink/55">ROOMS</div>
                <div className="text-xs text-ink/60">{rooms.length} entries</div>
              </div>

              {rooms.length === 0 ? (
                <div className="mt-6 rounded-2xl border border-ink/10 bg-paper/50 p-6 text-sm text-ink/70">
                  No room list found in the response. The raw JSON is still available below.
                </div>
              ) : (
                <div className="mt-6 overflow-hidden rounded-2xl border border-ink/10">
                  <div className="grid grid-cols-12 bg-paper-2/60 px-4 py-3 text-xs font-medium text-ink/70">
                    <div className="col-span-6">Room</div>
                    <div className="col-span-3 text-right">Area</div>
                    <div className="col-span-3 text-right">Confidence</div>
                  </div>
                  <div className="divide-y divide-ink/10 bg-paper/50">
                    {rooms.map((r, idx) => (
                      <div key={idx} className="grid grid-cols-12 px-4 py-3 text-sm">
                        <div className="col-span-6 truncate font-medium">
                          {r.name ?? `Room ${idx + 1}`}
                        </div>
                        <div className="col-span-3 text-right text-ink/70">
                          {r.area ?? '—'} {r.unit ?? ''}
                        </div>
                        <div className="col-span-3 text-right text-ink/70">
                          {typeof r.confidence === 'number'
                            ? `${Math.round(r.confidence * 100)}%`
                            : '—'}
                        </div>
                        {r.notes ? (
                          <div className="col-span-12 mt-2 text-xs text-ink/60">
                            {r.notes}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {boq.length > 0 && (
                <div className="mt-8">
                  <div className="flex items-center justify-between">
                    <div className="text-xs tracking-[0.2em] text-ink/55">BILL OF QUANTITIES</div>
                    <div className="text-xs text-ink/60">{boq.length} items</div>
                  </div>
                  <div className="mt-6 overflow-hidden rounded-2xl border border-ink/10">
                    <div className="grid grid-cols-12 bg-paper-2/60 px-4 py-3 text-xs font-medium text-ink/70">
                      <div className="col-span-6">Item</div>
                      <div className="col-span-2 text-right">Qty</div>
                      <div className="col-span-1 text-right">Unit</div>
                      <div className="col-span-3 text-right">Amount</div>
                    </div>
                    <div className="divide-y divide-ink/10 bg-paper/50">
                      {boq.map((b, idx) => (
                        <div key={idx} className="grid grid-cols-12 px-4 py-3 text-sm">
                          <div className="col-span-6 font-medium">
                            {b.item ?? `Item ${idx + 1}`}
                          </div>
                          <div className="col-span-2 text-right text-ink/70">
                            {b.quantity ?? '—'}
                          </div>
                          <div className="col-span-1 text-right text-ink/70">
                            {b.unit ?? ''}
                          </div>
                          <div className="col-span-3 text-right text-ink/70">
                            {formatInr(b.amount)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-6">
                <div className="text-xs tracking-[0.2em] text-ink/55">RAW JSON</div>
                <pre
                  className={cn(
                    'mt-3 max-h-[420px] overflow-auto rounded-2xl border border-ink/10 bg-[linear-gradient(180deg,hsl(var(--paper-2)/0.65),hsl(var(--paper)/0.65))] p-4 text-xs text-ink/75',
                    'shadow-[inset_0_1px_0_hsl(var(--ink)/0.08)]',
                  )}
                >
                  {pretty}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </div>
  )
}
