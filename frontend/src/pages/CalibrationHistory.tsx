import { ArrowLeft, Ruler } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Container from '@/components/Container'
import { API_BASE_URL } from '@/lib/api'

type CalibrationRecord = {
  analysis_job_id: string
  created_at?: string
  scale_factor?: number
  unit?: string
  real_world_distance?: number
  pixel_distance?: number
}

export default function CalibrationHistory() {
  const navigate = useNavigate()
  const [records, setRecords] = useState<CalibrationRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const token = await (window as any).Clerk?.session?.getToken()
        const response = await fetch(`${API_BASE_URL}/calibration/analysis-jobs/calibrations`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (response.ok) setRecords(await response.json())
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  return (
    <Container className="py-10 md:py-14">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2 text-sm text-ink/70 hover:text-ink"
      >
        <ArrowLeft className="h-4 w-4" /> Back
      </button>
      <div className="mt-6 flex items-center gap-3">
        <div className="rounded-xl border border-ink/15 bg-paper-2/50 p-3"><Ruler className="h-5 w-5" /></div>
        <div>
          <h1 className="font-display text-4xl tracking-tight">Calibration history</h1>
          <p className="mt-1 text-sm text-ink/65">Previously calibrated analysis files and their saved scale details.</p>
        </div>
      </div>

      <div className="mt-8 overflow-hidden rounded-xl border border-ink/15 bg-paper shadow-sm">
        {loading ? (
          <div className="p-6 text-sm text-ink/60">Loading previous calibrations…</div>
        ) : records.length === 0 ? (
          <div className="p-8 text-center text-sm text-ink/65">No manual calibrations have been saved yet.</div>
        ) : (
          <div className="divide-y divide-ink/10">
            {records.map((record) => (
              <button
                key={record.analysis_job_id}
                type="button"
                onClick={() => navigate(`/results/${record.analysis_job_id}`)}
                className="grid w-full gap-2 p-4 text-left text-sm transition hover:bg-paper-2/50 md:grid-cols-4 md:items-center"
              >
                <div>
                  <div className="font-medium text-ink">Analysis {record.analysis_job_id.slice(0, 8)}</div>
                  <div className="mt-1 text-xs text-ink/55">{record.created_at ? new Date(record.created_at).toLocaleString() : 'Saved calibration'}</div>
                </div>
                <div><span className="text-ink/55">Reference:</span> {record.real_world_distance ?? '—'} {record.unit ?? ''}</div>
                <div><span className="text-ink/55">Selected:</span> {record.pixel_distance?.toFixed(2) ?? '—'} px</div>
                <div><span className="text-ink/55">Scale:</span> {record.scale_factor?.toFixed(6) ?? '—'} {record.unit ?? ''}/px</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </Container>
  )
}
