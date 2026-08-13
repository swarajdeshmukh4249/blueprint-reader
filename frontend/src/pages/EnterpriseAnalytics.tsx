import { useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Area,
  AreaChart
} from 'recharts'
import { Calendar, Download, FolderKanban, FileText, IndianRupee, Timer, CheckCircle2 } from 'lucide-react'
import { useAuth } from '@clerk/clerk-react'
import { analyticsApi, blueprintFilesApi, projectsApi, type DashboardStats } from '@/lib/api'

type Project = {
  id: string
  name: string
  status?: string
  building_type?: string
  created_at?: string
}

type BlueprintFile = {
  id: string
  project_id?: string
  status?: string
  created_at?: string
  analyzed_at?: string
  analysis_time_seconds?: number
  processing_time_seconds?: number
  total_cost?: number
  total_area?: number
  analysis_result?: {
    total_cost?: number
    costs?: Record<string, number>
    materials?: Record<string, number>
    boq?: Array<{
      category?: string
      material_name?: string
      amount?: number
      quantity?: number
    }>
  }
}

const STATUS_COLORS: Record<string, string> = {
  Completed: '#4ade80',
  Processing: '#3b82f6',
  'In Queue': '#fbbf24',
  Failed: '#f87171'
}

const MATERIAL_COLORS = ['#7c3aed', '#3b82f6', '#34d399', '#f59e0b', '#f97316', '#94a3b8']

function formatCr(amount: number) {
  return `₹${(amount / 10000000).toFixed(1)} Cr`
}

function formatLakh(amount: number) {
  return `₹${(amount / 100000).toFixed(1)} Lakh`
}

function formatCost(amount: number) {
  if (!amount) return '—'
  if (amount >= 10000000) return formatCr(amount)
  if (amount >= 100000) return formatLakh(amount)
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

function fileCost(file: BlueprintFile): number {
  if (file.total_cost) return file.total_cost
  const costs = file.analysis_result?.costs
  if (costs?.['Total Estimated Cost']) return Number(costs['Total Estimated Cost']) || 0
  if (file.analysis_result?.total_cost) return Number(file.analysis_result.total_cost) || 0
  if (!file.analysis_result?.boq) return 0
  return file.analysis_result.boq.reduce((sum, item) => sum + (item.amount || 0), 0)
}

export default function EnterpriseAnalytics() {
  const { isLoaded, isSignedIn } = useAuth()
  const [loading, setLoading] = useState(true)
  const [projects, setProjects] = useState<Project[]>([])
  const [files, setFiles] = useState<BlueprintFile[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return

    const load = async () => {
      try {
        setLoading(true)
        const [projectList, fileList, dashStats] = await Promise.all([
          projectsApi.list(),
          blueprintFilesApi.list(undefined, 100),
          analyticsApi.getDashboardStats(),
        ])
        setProjects(Array.isArray(projectList) ? (projectList as Project[]) : [])
        setFiles(Array.isArray(fileList) ? (fileList as BlueprintFile[]) : [])
        setStats(dashStats as DashboardStats)
      } catch (error) {
        console.error('Failed to load analytics data:', error)
        setProjects([])
        setFiles([])
        setStats(null)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [isLoaded, isSignedIn])

  const metrics = useMemo(() => {
    const analyzedFiles = files.filter(
      (f) => f.status === 'analyzed' || f.status === 'completed' || !!f.analyzed_at || !!f.analysis_result
    )
    const analyzedCount = stats?.analyses_run ?? analyzedFiles.length
    const totalProjects = stats?.total_projects ?? projects.length
    const successRate = files.length
      ? (analyzedFiles.length / files.length) * 100
      : analyzedCount > 0
        ? 100
        : 0

    const totalEstimatedCost =
      stats?.total_estimated_value && stats.total_estimated_value > 0
        ? stats.total_estimated_value
        : analyzedFiles.reduce((sum, file) => sum + fileCost(file), 0)

    const analysisTimes = analyzedFiles
      .map((file) => file.analysis_time_seconds || file.processing_time_seconds || 0)
      .filter((value) => value > 0)
    const avgAnalysisTime =
      stats?.avg_analysis_seconds != null
        ? stats.avg_analysis_seconds
        : analysisTimes.length
          ? Math.round(analysisTimes.reduce((a, b) => a + b, 0) / analysisTimes.length)
          : null

    const projectMap = new Map(projects.map((project) => [project.id, project]))
    const costByProject = new Map<string, number>()
    const costByMaterial = new Map<string, number>()

    analyzedFiles.forEach((file) => {
      const project = projectMap.get(file.project_id || '')
      const projectName = project?.name || 'Untitled Project'
      const amount = fileCost(file)
      costByProject.set(projectName, (costByProject.get(projectName) || 0) + amount)

      const materials = file.analysis_result?.materials
      if (materials && typeof materials === 'object') {
        Object.entries(materials).forEach(([name, value]) => {
          const num = typeof value === 'number' ? value : Number(value) || 0
          // treat quantity as proxy weight for chart when no BOQ amounts
          costByMaterial.set(name, (costByMaterial.get(name) || 0) + num)
        })
      }
      file.analysis_result?.boq?.forEach((item) => {
        const materialName = item.material_name || item.category || 'Others'
        const lineAmount = item.amount || 0
        if (lineAmount > 0) {
          costByMaterial.set(materialName, (costByMaterial.get(materialName) || 0) + lineAmount)
        }
      })
    })

    const topProjects = [...costByProject.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, cost]) => {
        const match = projects.find((p) => p.name === name)
        return {
          name,
          type: match?.building_type || 'General',
          cost
        }
      })

    const materials = [...costByMaterial.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([name, amount], index, arr) => {
        const total = arr.reduce((sum, item) => sum + item[1], 0) || 1
        return {
          name,
          amount,
          percentage: (amount / total) * 100,
          color: MATERIAL_COLORS[index % MATERIAL_COLORS.length]
        }
      })

    // Real daily analysis counts (no inflation)
    const filesByDay = new Map<string, { count: number; cost: number; sortKey: number }>()
    analyzedFiles.forEach((file) => {
      const date = file.analyzed_at || file.created_at
      if (!date) return
      const d = new Date(date)
      const day = d.toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
      const prev = filesByDay.get(day) || { count: 0, cost: 0, sortKey: d.getTime() }
      prev.count += 1
      prev.cost += fileCost(file)
      filesByDay.set(day, prev)
    })

    const trend = [...filesByDay.entries()]
      .sort((a, b) => a[1].sortKey - b[1].sortKey)
      .slice(-8)
      .map(([day, data]) => ({ day, value: data.count }))

    // Cumulative cost over time from real file costs
    let running = 0
    const costTrend = [...filesByDay.entries()]
      .sort((a, b) => a[1].sortKey - b[1].sortKey)
      .slice(-8)
      .map(([day, data]) => {
        running += data.cost
        return { day, value: running }
      })

    // Prefer monthly project creation from stats API when available
    const projectTrend =
      stats?.projects_by_month?.some((m) => m.count > 0)
        ? stats.projects_by_month.map((m) => ({
            day: m.month.split(' ')[0],
            value: m.count,
          }))
        : trend

    const statusCounts = {
      Completed: projects.filter((p) => p.status === 'completed').length,
      Processing: projects.filter((p) => p.status === 'active').length,
      'In Queue': projects.filter((p) => p.status === 'draft').length,
      Failed: projects.filter((p) => p.status === 'on_hold' || p.status === 'failed').length
    }

    const statusData = Object.entries(statusCounts)
      .filter(([, value]) => value > 0)
      .map(([name, value]) => ({ name, value }))

    const distribution = [
      { range: '0-10', count: 0 },
      { range: '10-20', count: 0 },
      { range: '20-30', count: 0 },
      { range: '30-40', count: 0 },
      { range: '40-50', count: 0 },
      { range: '50+', count: 0 }
    ]
    analysisTimes.forEach((time) => {
      if (time < 10) distribution[0].count += 1
      else if (time < 20) distribution[1].count += 1
      else if (time < 30) distribution[2].count += 1
      else if (time < 40) distribution[3].count += 1
      else if (time < 50) distribution[4].count += 1
      else distribution[5].count += 1
    })

    const dateRangeLabel = (() => {
      const dates = files
        .map((f) => f.created_at)
        .filter(Boolean)
        .map((d) => new Date(d as string).getTime())
      if (!dates.length) return 'No data yet'
      const min = new Date(Math.min(...dates))
      const max = new Date(Math.max(...dates))
      const fmt = (d: Date) =>
        d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
      return `${fmt(min)} – ${fmt(max)}`
    })()

    return {
      totalProjects,
      analyzedCount,
      totalEstimatedCost,
      avgAnalysisTime,
      successRate,
      topProjects,
      materials,
      trend: projectTrend,
      costTrend,
      statusData,
      distribution,
      dateRangeLabel,
      hasDistribution: distribution.some((d) => d.count > 0),
    }
  }, [files, projects, stats])

  const exportCsv = () => {
    const rows = [
      ['Metric', 'Value'],
      ['Total Projects', String(metrics.totalProjects)],
      ['Blueprints Analyzed', String(metrics.analyzedCount)],
      ['Total Estimated Cost', String(metrics.totalEstimatedCost)],
      ['Avg Analysis Time', metrics.avgAnalysisTime != null ? String(metrics.avgAnalysisTime) : ''],
      ['Success Rate', metrics.successRate.toFixed(1)],
      ['Total Area (sq ft)', String(stats?.total_area_sqft ?? '')],
    ]
    const blob = new Blob([rows.map((r) => r.join(',')).join('\n')], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `analytics-overview-${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(link)
    link.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(link)
  }

  if (!isLoaded || loading) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center">
        <div className="text-ink/70">Loading analytics...</div>
      </div>
    )
  }

  if (!isSignedIn) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center">
        <div className="text-ink/70">Please sign in to view analytics.</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-paper px-6 py-6 lg:px-8 space-y-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-ink">Analytics Overview</h1>
          <p className="text-ink/60 mt-1">Track insights and performance of your projects.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="inline-flex items-center gap-2 rounded-xl border border-ink/15 bg-paper-2 px-4 py-2 text-sm text-ink/90">
            <Calendar className="h-4 w-4" />
            {metrics.dateRangeLabel}
          </button>
          <button
            onClick={exportCsv}
            className="inline-flex items-center gap-2 rounded-xl border border-ink/15 bg-paper-2 px-4 py-2 text-sm text-ink/90 hover:bg-paper"
          >
            <Download className="h-4 w-4" />
            Export Report
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
        {[
          { label: 'Total Projects', value: metrics.totalProjects, icon: FolderKanban, accent: 'text-purple-400' },
          { label: 'Blueprints Analyzed', value: metrics.analyzedCount, icon: FileText, accent: 'text-blue-400' },
          {
            label: 'Total Estimated Cost',
            value: formatCost(metrics.totalEstimatedCost),
            icon: IndianRupee,
            accent: 'text-emerald-400'
          },
          {
            label: 'Avg. Analysis Time',
            value: metrics.avgAnalysisTime != null ? `${metrics.avgAnalysisTime} sec` : '—',
            icon: Timer,
            accent: 'text-amber-400'
          },
          {
            label: 'Success Rate',
            value: files.length || metrics.analyzedCount ? `${metrics.successRate.toFixed(1)}%` : '—',
            icon: CheckCircle2,
            accent: 'text-emerald-400'
          }
        ].map((card) => (
          <div key={card.label} className="rounded-2xl border border-ink/15 bg-paper-2 p-4">
            <div className="flex items-start justify-between">
              <p className="text-sm text-ink/70">{card.label}</p>
              <card.icon className={`h-5 w-5 ${card.accent}`} />
            </div>
            <p className="mt-2 text-4xl font-semibold text-ink">{card.value}</p>
            <p className="mt-2 text-sm text-ink/50">
              {stats?.trends.projects_this_month
                ? `+${stats.trends.projects_this_month} projects this month`
                : 'Based on your data'}
            </p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-3 xl:grid-cols-12">
        <div className="rounded-2xl border border-ink/15 bg-paper-2 p-4 xl:col-span-5">
          <h2 className="text-xl font-medium text-ink mb-4">Projects Trend</h2>
          <div className="h-56">
            {metrics.trend.length === 0 ? (
              <div className="h-full flex items-center justify-center text-sm text-ink/50">No trend data yet</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metrics.trend}>
                  <defs>
                    <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.45} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#334155" strokeOpacity={0.25} vertical={false} />
                  <XAxis dataKey="day" stroke="#94a3b8" tickLine={false} axisLine={false} />
                  <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip contentStyle={{ borderRadius: 12, borderColor: '#334155', background: '#0f172a' }} />
                  <Area type="monotone" dataKey="value" stroke="#818cf8" fill="url(#trendFill)" strokeWidth={2.5} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-ink/15 bg-paper-2 p-4 xl:col-span-4">
          <h2 className="text-xl font-medium text-ink mb-4">Estimated Cost Over Time</h2>
          <div className="h-56">
            {metrics.costTrend.length === 0 ? (
              <div className="h-full flex items-center justify-center text-sm text-ink/50">No cost data yet</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metrics.costTrend}>
                  <defs>
                    <linearGradient id="costFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4ade80" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#4ade80" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#334155" strokeOpacity={0.25} vertical={false} />
                  <XAxis dataKey="day" stroke="#94a3b8" tickLine={false} axisLine={false} />
                  <YAxis
                    stroke="#94a3b8"
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) =>
                      value >= 10000000
                        ? `₹${Math.round(value / 10000000)} Cr`
                        : value >= 100000
                          ? `₹${Math.round(value / 100000)} L`
                          : `₹${Math.round(value)}`
                    }
                  />
                  <Tooltip
                    contentStyle={{ borderRadius: 12, borderColor: '#334155', background: '#0f172a' }}
                    formatter={(value: number) => formatCost(value)}
                  />
                  <Area type="monotone" dataKey="value" stroke="#4ade80" fill="url(#costFill)" strokeWidth={2.5} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-ink/15 bg-paper-2 p-4 xl:col-span-3">
          <h2 className="text-xl font-medium text-ink mb-4">Projects by Status</h2>
          <div className="h-56">
            {metrics.statusData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-sm text-ink/50">No projects yet</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={metrics.statusData} dataKey="value" innerRadius={55} outerRadius={85} paddingAngle={4}>
                    {metrics.statusData.map((entry) => (
                      <Cell key={entry.name} fill={STATUS_COLORS[entry.name]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: 12, borderColor: '#334155', background: '#0f172a' }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 xl:grid-cols-12">
        <div className="rounded-2xl border border-ink/15 bg-paper-2 p-4 xl:col-span-4">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-medium text-ink">Top Projects by Estimated Cost</h2>
          </div>
          <div className="space-y-3">
            {metrics.topProjects.length === 0 ? (
              <p className="text-sm text-ink/60">No project cost data yet.</p>
            ) : (
              metrics.topProjects.map((project) => (
                <div key={project.name} className="rounded-xl border border-ink/10 bg-paper px-3 py-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-ink">{project.name}</p>
                    <p className="text-sm font-semibold text-ink">{formatCost(project.cost)}</p>
                  </div>
                  <p className="text-xs text-ink/50 mt-1 capitalize">{project.type}</p>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-ink/15 bg-paper-2 p-4 xl:col-span-4">
          <h2 className="text-xl font-medium text-ink mb-4">Material Usage Overview</h2>
          {metrics.materials.length === 0 ? (
            <div className="h-56 flex items-center justify-center text-sm text-ink/50">No material data yet</div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={metrics.materials} dataKey="amount" innerRadius={45} outerRadius={80}>
                      {metrics.materials.map((entry) => (
                        <Cell key={entry.name} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ borderRadius: 12, borderColor: '#334155', background: '#0f172a' }}
                      formatter={(value: number) => value.toLocaleString()}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2">
                {metrics.materials.map((item) => (
                  <div key={item.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-ink/80">
                      <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                      {item.name}
                    </div>
                    <span className="text-ink/70">{item.percentage.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-ink/15 bg-paper-2 p-4 xl:col-span-4">
          <h2 className="text-xl font-medium text-ink mb-4">Analysis Time Distribution</h2>
          <div className="h-56">
            {!metrics.hasDistribution ? (
              <div className="h-full flex items-center justify-center text-sm text-ink/50">
                No analysis timing data yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metrics.distribution}>
                  <CartesianGrid stroke="#334155" strokeOpacity={0.25} vertical={false} />
                  <XAxis dataKey="range" stroke="#94a3b8" tickLine={false} axisLine={false} />
                  <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip contentStyle={{ borderRadius: 12, borderColor: '#334155', background: '#0f172a' }} />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]} fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
