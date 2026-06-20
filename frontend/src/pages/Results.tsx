import { Download, RotateCcw, FileText, Calculator, MessageSquare, BarChart3, Save, Check, Ruler, Expand } from 'lucide-react'
import { NavLink, useParams, useNavigate } from 'react-router-dom'
import Container from '@/components/Container'
import { cn } from '@/lib/utils'
import { useAnalysisStore } from '@/stores/useAnalysisStore'
import type { AnalyzeBlueprintRoom } from '@/types/analysis'
import { useState, useEffect } from 'react'
import { PieChart, Pie, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import ScaleCalibrationPanel from '@/components/ScaleCalibration/ScaleCalibrationPanel'

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
  const { fileId } = useParams<{ fileId?: string }>()
  const navigate = useNavigate()
  const filename = useAnalysisStore((s) => s.filename)
  const result = useAnalysisStore((s) => s.result)
  const reset = useAnalysisStore((s) => s.reset)
  const [editableBoq, setEditableBoq] = useState<any[]>([])
  const [showFinalBoq, setShowFinalBoq] = useState(false)
  const [activeTab, setActiveTab] = useState<'rooms' | 'boq' | 'charts' | 'comments'>('rooms')
  const [comments, setComments] = useState<{id: string, user_id: string, user_name: string, content: string, created_at: string}[]>([])
  const [newComment, setNewComment] = useState('')
  const [boqFinalized, setBoqFinalized] = useState(false)
  const [showCalibration, setShowCalibration] = useState(false)
  const [blueprintImageUrl, setBlueprintImageUrl] = useState<string | null>(null)

  useEffect(() => {
    if (result?.boq) {
      setEditableBoq(result.boq.map((item: any) => ({
        ...item,
        rate: item.rate || (item.quantity && item.amount ? item.amount / item.quantity : 0)
      })))
    }
  }, [result])

  useEffect(() => {
    // Fetch blueprint file data to get image URL if fileId is provided
    if (fileId) {
      fetchBlueprintFileData(fileId)
      fetchComments(fileId)
    }
  }, [fileId])

  const fetchComments = async (jobId: string) => {
    try {
      const token = await (window as any).Clerk?.session?.getToken()
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(`${API_BASE_URL}/analysis/analysis-jobs/${jobId}/comments`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setComments(data)
      }
    } catch (error) {
      console.error('Failed to fetch comments:', error)
    }
  }

  const fetchBlueprintFileData = async (fileId: string) => {
    try {
      const token = await (window as any).Clerk?.session?.getToken()
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(`${API_BASE_URL}/blueprint-files/${fileId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const fileData = await response.json()
        if (fileData.file_path) {
          setBlueprintImageUrl(fileData.file_path)
        }
      }
    } catch (error) {
      console.error('Failed to fetch blueprint file data:', error)
    }
  }

  const handleCalibrationApplied = async (calibrationData: any) => {
    try {
      const token = await (window as any).Clerk?.session?.getToken()
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(
        `${API_BASE_URL}/calibration/analysis-jobs/${fileId}/scale-calibration`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(calibrationData)
        }
      )
      if (response.ok) {
        const result = await response.json()
        console.log('Calibration saved:', result)
        setShowCalibration(false)
      } else {
        console.error('Failed to save calibration')
      }
    } catch (error) {
      console.error('Error saving calibration:', error)
    }
  }

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

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

  const costBreakdownData = boq.length > 0 ? boq.map((item, idx) => ({
    name: item.item || `Item ${idx + 1}`,
    value: item.amount || 0
  })).slice(0, 6) : []

  const materialUsageData = boq.length > 0 ? boq.slice(0, 5).map((item, idx) => ({
    name: item.item || `Item ${idx + 1}`,
    quantity: item.quantity || 0,
    amount: item.amount || 0
  })) : []

  const handleAddComment = async () => {
    if (newComment.trim() && fileId) {
      try {
        const token = await (window as any).Clerk?.session?.getToken()
        const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
        const response = await fetch(`${API_BASE_URL}/analysis/analysis-jobs/${fileId}/comments`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ content: newComment })
        })
        if (response.ok) {
          const newCommentData = await response.json()
          setComments([...comments, newCommentData])
          setNewComment('')
        } else {
          console.error('Failed to add comment')
        }
      } catch (error) {
        console.error('Error adding comment:', error)
      }
    }
  }

  const handleFinalizeBoq = () => {
    setBoqFinalized(true)
    setShowFinalBoq(true)
  }

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
            {fileId && blueprintImageUrl && (
              <button
                type="button"
                onClick={() => setShowCalibration(true)}
                className="inline-flex items-center gap-2 rounded-full border border-ink/12 bg-paper/60 px-4 py-2 text-sm text-ink/80 transition hover:bg-paper hover:text-ink"
              >
                <Ruler className="h-4 w-4" />
                Calibrate Scale
              </button>
            )}
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
          {/* Summary Sidebar */}
          <div className="md:col-span-3">
            <div className="rounded-lg border border-ink/20 bg-paper shadow-sm p-5">
              <div className="text-xs font-semibold text-ink/50 uppercase tracking-wider">SUMMARY</div>
              <div className="mt-4 space-y-3">
                {/* File Preview Card */}
                {fileId && blueprintImageUrl && (
                  <div className="rounded-lg border border-ink/15 bg-paper-2/50 p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs text-ink/60">Blueprint Preview</div>
                      <button
                        onClick={() => navigate(`/viewer?job_id=${fileId}`)}
                        className="text-ink/60 hover:text-ink transition-colors"
                        title="Expand to full viewer"
                      >
                        <Expand className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="relative rounded-lg overflow-hidden bg-paper border border-ink/10 aspect-video cursor-pointer" onClick={() => navigate(`/viewer?job_id=${fileId}`)}>
                      <img
                        src={blueprintImageUrl}
                        alt="Blueprint preview"
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 bg-ink/0 hover:bg-ink/10 transition-colors flex items-center justify-center opacity-0 hover:opacity-100">
                        <Expand className="h-6 w-6 text-ink" />
                      </div>
                    </div>
                  </div>
                )}
                <div className="rounded-lg border border-ink/15 bg-paper-2/50 p-3">
                  <div className="text-xs text-ink/60">Rooms</div>
                  <div className="mt-1 font-display text-2xl tracking-tight">
                    {roomCount}
                  </div>
                </div>
                <div className="rounded-lg border border-ink/15 bg-paper-2/50 p-3">
                  <div className="text-xs text-ink/60">Total Area</div>
                  <div className="mt-1 font-display text-2xl tracking-tight">
                    {totals?.total_area ?? '—'}{' '}
                    <span className="text-sm text-ink/60">{totals?.unit ?? ''}</span>
                  </div>
                </div>
                {typeof totals?.boq_total === 'number' && totals.boq_total > 0 && (
                  <div className="rounded-lg border border-ink/15 bg-paper-2/50 p-3">
                    <div className="text-xs text-ink/60">BOQ Total</div>
                    <div className="mt-1 font-display text-2xl tracking-tight">
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
                  className="inline-flex w-full items-center justify-center rounded-lg bg-ink px-4 py-2 text-sm font-medium text-paper transition hover:bg-ink/90"
                >
                  Analyze another file
                </NavLink>
              </div>
            </div>
          </div>

          {/* Main Content with Tabs */}
          <div className="md:col-span-9">
            <div className="rounded-lg border border-ink/20 bg-paper shadow-sm">
              {/* Tab Navigation */}
              <div className="flex space-x-1 border-b border-ink/20 px-5 pt-5">
                {[
                  { id: 'rooms' as const, label: 'Rooms', icon: FileText },
                  { id: 'boq' as const, label: 'BOQ', icon: Calculator },
                  { id: 'charts' as const, label: 'Charts', icon: BarChart3 },
                  { id: 'comments' as const, label: 'Comments', icon: MessageSquare },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2 text-xs font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-accent text-accent'
                        : 'border-transparent text-ink/60 hover:text-ink'
                    }`}
                  >
                    <tab.icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="p-5">
                {activeTab === 'rooms' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-sm font-semibold text-ink">Rooms ({rooms.length})</div>
                    </div>
                    {rooms.length === 0 ? (
                      <div className="rounded-lg border border-ink/15 bg-paper-2/50 p-6 text-sm text-ink/70">
                        No room list found in the response.
                      </div>
                    ) : (
                      <div className="overflow-hidden rounded-lg border border-ink/15">
                        <div className="grid grid-cols-12 bg-paper-2/60 px-4 py-3 text-xs font-medium text-ink/70">
                          <div className="col-span-6">Room</div>
                          <div className="col-span-3 text-right">Area</div>
                          <div className="col-span-3 text-right">Confidence</div>
                        </div>
                        <div className="divide-y divide-ink/10 bg-paper-2/50 max-h-96 overflow-y-auto">
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
                  </div>
                )}

                {activeTab === 'boq' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-sm font-semibold text-ink">Bill of Quantities ({editableBoq.length} items)</div>
                      <div className="flex gap-2">
                        {!boqFinalized && (
                          <button
                            onClick={handleFinalizeBoq}
                            className="flex items-center gap-2 px-3 py-1.5 bg-accent text-paper rounded-lg text-xs font-medium hover:bg-accent/90"
                          >
                            <Check className="h-3 w-3" />
                            Finalize Changes
                          </button>
                        )}
                        {boqFinalized && (
                          <button
                            onClick={() => download('final-boq.csv', toCsv(editableBoq.map((b, idx) => ({
                              name: b.item ?? `Item ${idx + 1}`,
                              area: b.quantity,
                              unit: b.unit,
                              confidence: b.rate,
                              notes: `Amount: ${formatInr(b.amount)}`
                            }))), 'text/csv')}
                            className="flex items-center gap-2 px-3 py-1.5 bg-green-500 text-paper rounded-lg text-xs font-medium hover:bg-green-500/90"
                          >
                            <Download className="h-3 w-3" />
                            Download Final BOQ
                          </button>
                        )}
                      </div>
                    </div>
                    {boq.length === 0 ? (
                      <div className="rounded-lg border border-ink/15 bg-paper-2/50 p-6 text-sm text-ink/70">
                        No BOQ data found.
                      </div>
                    ) : (
                      <div className="overflow-hidden rounded-lg border border-ink/15">
                        <div className="grid grid-cols-12 bg-paper-2/60 px-4 py-3 text-xs font-medium text-ink/70">
                          <div className="col-span-5">Item</div>
                          <div className="col-span-2 text-right">Qty</div>
                          <div className="col-span-2 text-right">Rate</div>
                          <div className="col-span-1 text-right">Unit</div>
                          <div className="col-span-2 text-right">Amount</div>
                        </div>
                        <div className="divide-y divide-ink/10 bg-paper-2/50 max-h-96 overflow-y-auto">
                          {editableBoq.map((b, idx) => (
                            <div key={idx} className="grid grid-cols-12 px-4 py-3 text-sm">
                              <div className="col-span-5 font-medium">
                                {b.item ?? `Item ${idx + 1}`}
                              </div>
                              <div className="col-span-2 text-right">
                                <input
                                  type="number"
                                  value={b.quantity ?? ''}
                                  disabled={boqFinalized}
                                  onChange={(e) => {
                                    const newBoq = [...editableBoq]
                                    newBoq[idx].quantity = parseFloat(e.target.value) || 0
                                    newBoq[idx].amount = (newBoq[idx].quantity || 0) * (newBoq[idx].rate || 0)
                                    setEditableBoq(newBoq)
                                  }}
                                  className={`w-16 text-right border rounded px-1 py-0.5 text-ink/70 ${boqFinalized ? 'bg-paper-2/50 cursor-not-allowed' : ''}`}
                                />
                              </div>
                              <div className="col-span-2 text-right">
                                <input
                                  type="number"
                                  value={b.rate ?? ''}
                                  disabled={boqFinalized}
                                  onChange={(e) => {
                                    const newBoq = [...editableBoq]
                                    newBoq[idx].rate = parseFloat(e.target.value) || 0
                                    newBoq[idx].amount = (newBoq[idx].quantity || 0) * (newBoq[idx].rate || 0)
                                    setEditableBoq(newBoq)
                                  }}
                                  className={`w-20 text-right border rounded px-1 py-0.5 text-ink/70 ${boqFinalized ? 'bg-paper-2/50 cursor-not-allowed' : ''}`}
                                />
                              </div>
                              <div className="col-span-1 text-right text-ink/70">
                                {b.unit ?? ''}
                              </div>
                              <div className="col-span-2 text-right text-ink/70">
                                {formatInr(b.amount)}
                              </div>
                            </div>
                          ))}
                        </div>
                        <div className="bg-paper-2/60 px-4 py-3 text-right">
                          <div className="text-sm font-medium text-ink">
                            Total: {formatInr(editableBoq.reduce((sum, item) => sum + (item.amount || 0), 0))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'charts' && (
                  <div>
                    <div className="text-sm font-semibold text-ink mb-4">Cost Breakdown Visualization</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {/* Cost Breakdown Pie Chart */}
                  <div className="rounded-lg border border-ink/15 bg-paper-2/50 p-4">
                    <div className="text-xs font-medium text-ink/70 mb-3">Cost Distribution</div>
                    {costBreakdownData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={280}>
                        <PieChart>
                          <Pie
                            data={costBreakdownData}
                            cx="50%"
                            cy="45%"
                            labelLine={false}
                            label={false}
                            outerRadius={75}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {costBreakdownData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value: number, name: string) => [formatInr(value), name]} />
                          <Legend
                            layout="horizontal"
                            verticalAlign="bottom"
                            align="center"
                            wrapperStyle={{ fontSize: 11, lineHeight: '1.4' }}
                            formatter={(value: string) => value.length > 22 ? `${value.slice(0, 22)}…` : value}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="text-sm text-ink/60 text-center py-8">No data available</div>
                    )}
                  </div>

                                        {/* Material Usage Bar Chart */}
                  <div className="rounded-lg border border-ink/15 bg-paper-2/50 p-4">
                    <div className="text-xs font-medium text-ink/70 mb-3">Material Usage</div>
                    {materialUsageData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={Math.max(250, materialUsageData.length * 45)}>
                        <BarChart data={materialUsageData} layout="vertical" margin={{ left: 10, right: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" />
                          <YAxis
                            dataKey="name"
                            type="category"
                            width={150}
                            tick={{ fontSize: 11 }}
                            tickFormatter={(value: string) => value.length > 24 ? `${value.slice(0, 24)}…` : value}
                          />
                          <Tooltip formatter={(value) => formatInr(value as number)} />
                          <Bar dataKey="amount" fill="#3b82f6" />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="text-sm text-ink/60 text-center py-8">No data available</div>
                    )}
                  </div>

                      {/* KPI Cards */}
                      <div className="md:col-span-2 rounded-lg border border-ink/15 bg-paper-2/50 p-4">
                        <div className="text-xs font-medium text-ink/70 mb-3">Key Metrics</div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          <div className="rounded-lg bg-accent/10 p-3">
                            <div className="text-xs text-accent font-medium">Total Items</div>
                            <div className="mt-1 text-xl font-bold text-ink">{boq.length}</div>
                          </div>
                          <div className="rounded-lg bg-green-500/10 p-3">
                            <div className="text-xs text-green-500 font-medium">Total Qty</div>
                            <div className="mt-1 text-xl font-bold text-ink">{boq.reduce((sum, item) => sum + (item.quantity || 0), 0).toLocaleString()}</div>
                          </div>
                          <div className="rounded-lg bg-yellow-500/10 p-3">
                            <div className="text-xs text-yellow-500 font-medium">Avg Rate</div>
                            <div className="mt-1 text-xl font-bold text-ink">{boq.length > 0 ? formatInr(boq.reduce((sum, item) => sum + (item.rate || 0), 0) / boq.length) : '—'}</div>
                          </div>
                          <div className="rounded-lg bg-purple-500/10 p-3">
                            <div className="text-xs text-purple-500 font-medium">Total Cost</div>
                            <div className="mt-1 text-xl font-bold text-ink">{formatInr(totals?.boq_total || 0)}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'comments' && (
                  <div>
                    <div className="text-sm font-semibold text-ink mb-4">Comments & Collaboration</div>
                    
                    {/* Add Comment Form */}
                    <div className="mb-4">
                      <textarea
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="Add a comment..."
                        className="w-full rounded-lg border border-ink/15 bg-paper-2/50 px-4 py-3 text-sm text-ink placeholder:text-ink/40 focus:outline-none focus:ring-2 focus:ring-accent/50"
                        rows={3}
                      />
                      <div className="mt-2 flex justify-end">
                        <button
                          onClick={handleAddComment}
                          className="flex items-center gap-2 px-4 py-2 bg-accent text-paper rounded-lg text-xs font-medium hover:bg-accent/90"
                        >
                          <MessageSquare className="h-3 w-3" />
                          Add Comment
                        </button>
                      </div>
                    </div>

                    {/* Comments List */}
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {comments.length === 0 ? (
                        <div className="rounded-lg border border-ink/15 bg-paper-2/50 p-6 text-sm text-ink/60 text-center">
                          No comments yet. Be the first to add one!
                        </div>
                      ) : (
                        comments.map((comment) => (
                          <div key={comment.id} className="rounded-lg border border-ink/15 bg-paper-2/50 p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <div className="h-6 w-6 rounded-full bg-accent/10 flex items-center justify-center">
                                  <span className="text-xs font-medium text-accent">{comment.user_name[0]}</span>
                                </div>
                                <span className="text-xs font-medium text-ink">{comment.user_name}</span>
                              </div>
                              <span className="text-xs text-ink/40">{new Date(comment.created_at).toLocaleString()}</span>
                            </div>
                            <p className="text-sm text-ink/80">{comment.content}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </Container>

      {/* Scale Calibration Modal */}
      {showCalibration && fileId && blueprintImageUrl && (
        <ScaleCalibrationPanel
          imageUrl={blueprintImageUrl}
          onClose={() => setShowCalibration(false)}
          onScaleApplied={handleCalibrationApplied}
        />
      )}
    </div>
  )
}
