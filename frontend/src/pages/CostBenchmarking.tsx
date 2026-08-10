import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { costBenchmarkApi, projectsApi } from '../lib/api'
import { ArrowLeft, TrendingUp, TrendingDown, Minus, BarChart3, Plus, Trash2 } from 'lucide-react'

interface CostBenchmark {
  id: string
  project_id: string
  category: string
  metric_name: string
  your_value: number
  your_unit: string | null
  benchmark_value: number
  benchmark_unit: string | null
  benchmark_source: string | null
  variance_percentage: number | null
  variance_status: string | null
  region: string | null
  building_type: string | null
  project_size_category: string | null
  created_at: string
}

interface ProjectComparison {
  project_id: string
  project_name: string
  metrics: Array<{
    metric: string
    your_value: number
    benchmark_value: number
    variance_percentage: number
    status: string
  }>
}

interface Project {
  id: string
  name: string
  location_state?: string
  building_type?: string
}

export default function CostBenchmarking() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  
  const [benchmarks, setBenchmarks] = useState<CostBenchmark[]>([])
  const [comparison, setComparison] = useState<ProjectComparison | null>(null)
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Form state
  const [category, setCategory] = useState('')
  const [metricName, setMetricName] = useState('')
  const [yourValue, setYourValue] = useState('')
  const [yourUnit, setYourUnit] = useState('')
  const [benchmarkValue, setBenchmarkValue] = useState('')
  const [benchmarkUnit, setBenchmarkUnit] = useState('')
  const [benchmarkSource, setBenchmarkSource] = useState('')
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    loadProject()
    loadBenchmarks()
    loadComparison()
  }, [projectId])

  const loadProject = async () => {
    try {
      const data: Project = await projectsApi.get(projectId!)
      setProject(data)
    } catch (err) {
      console.error('Failed to load project:', err)
    }
  }

  const loadBenchmarks = async () => {
    try {
      const data: CostBenchmark[] = await costBenchmarkApi.list(projectId!)
      setBenchmarks(data)
    } catch (err) {
      console.error('Failed to load benchmarks:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadComparison = async () => {
    try {
      const data: ProjectComparison = await costBenchmarkApi.compare(projectId!)
      setComparison(data)
    } catch (err) {
      console.error('Failed to load comparison:', err)
    }
  }

  const handleAddBenchmark = async () => {
    if (!category || !metricName || !yourValue || !benchmarkValue) {
      setError('Please fill in all required fields')
      return
    }

    setAdding(true)
    setError(null)

    try {
      const newBenchmark: CostBenchmark = await costBenchmarkApi.create({
        project_id: projectId!,
        category,
        metric_name: metricName,
        your_value: parseFloat(yourValue),
        your_unit: yourUnit || undefined,
        benchmark_value: parseFloat(benchmarkValue),
        benchmark_unit: benchmarkUnit || undefined,
        benchmark_source: benchmarkSource || undefined,
        region: project?.location_state,
        building_type: project?.building_type,
      })
      
      setBenchmarks([newBenchmark, ...benchmarks])
      setShowAddForm(false)
      setCategory('')
      setMetricName('')
      setYourValue('')
      setYourUnit('')
      setBenchmarkValue('')
      setBenchmarkUnit('')
      setBenchmarkSource('')
      
      // Reload comparison
      loadComparison()
    } catch (err: any) {
      setError(err.message || 'Failed to create benchmark')
    } finally {
      setAdding(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this benchmark?')) return
    
    try {
      await costBenchmarkApi.delete(id)
      setBenchmarks(benchmarks.filter(b => b.id !== id))
      loadComparison()
    } catch (err) {
      console.error('Failed to delete benchmark:', err)
    }
  }

  const getVarianceIcon = (status: string | null) => {
    if (status === 'above') return <TrendingUp className="w-4 h-4 text-red-600" />
    if (status === 'below') return <TrendingDown className="w-4 h-4 text-green-600" />
    return <Minus className="w-4 h-4 text-ink/60" />
  }

  const getVarianceColor = (status: string | null) => {
    if (status === 'above') return 'text-red-600'
    if (status === 'below') return 'text-green-600'
    return 'text-ink/60'
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <div className="min-h-screen bg-ink/5 p-8">
      <div className="max-w-6xl mx-auto">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center text-ink/60 hover:text-ink mb-6"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back
        </button>

        <div className="bg-paper-2 rounded-xl border p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-ink">Cost Benchmarking</h1>
              <p className="text-ink/60 mt-1">{project?.name || 'Project'}</p>
            </div>
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              {showAddForm ? 'Cancel' : 'Add Benchmark'}
            </button>
          </div>

          {showAddForm && (
            <div className="bg-ink/5 rounded-lg p-6 mb-6">
              <h2 className="text-lg font-semibold text-ink mb-4">Add New Benchmark</h2>
              
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-ink/80 mb-2">
                    Category *
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="">Select category...</option>
                    <option value="cost_per_sqft">Cost per Sq Ft</option>
                    <option value="material_usage">Material Usage</option>
                    <option value="construction_time">Construction Time</option>
                    <option value="labor_cost">Labor Cost</option>
                    <option value="overhead">Overhead</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-ink/80 mb-2">
                    Metric Name *
                  </label>
                  <input
                    type="text"
                    value={metricName}
                    onChange={(e) => setMetricName(e.target.value)}
                    placeholder="e.g., Steel Usage, Cement Usage"
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-ink/80 mb-2">
                    Your Value *
                  </label>
                  <input
                    type="number"
                    value={yourValue}
                    onChange={(e) => setYourValue(e.target.value)}
                    placeholder="Enter your value"
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-ink/80 mb-2">
                    Your Unit
                  </label>
                  <input
                    type="text"
                    value={yourUnit}
                    onChange={(e) => setYourUnit(e.target.value)}
                    placeholder="e.g., sq ft, kg/sq ft, days"
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-ink/80 mb-2">
                    Benchmark Value *
                  </label>
                  <input
                    type="number"
                    value={benchmarkValue}
                    onChange={(e) => setBenchmarkValue(e.target.value)}
                    placeholder="Enter industry benchmark"
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-ink/80 mb-2">
                    Benchmark Unit
                  </label>
                  <input
                    type="text"
                    value={benchmarkUnit}
                    onChange={(e) => setBenchmarkUnit(e.target.value)}
                    placeholder="e.g., sq ft, kg/sq ft, days"
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-ink/80 mb-2">
                    Benchmark Source
                  </label>
                  <input
                    type="text"
                    value={benchmarkSource}
                    onChange={(e) => setBenchmarkSource(e.target.value)}
                    placeholder="e.g., DSR 2023, Industry Average"
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
              </div>

              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}

              <div className="mt-4 flex gap-3">
                <button
                  onClick={handleAddBenchmark}
                  disabled={adding}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
                >
                  {adding ? 'Adding...' : 'Add Benchmark'}
                </button>
                <button
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 border rounded-lg hover:bg-ink/5"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Auto-comparison from project data */}
          {comparison && comparison.metrics.length > 0 && (
            <div className="bg-blue-50 rounded-lg p-6 mb-6 border border-blue-200">
              <div className="flex items-center mb-4">
                <BarChart3 className="w-5 h-5 text-blue-600 mr-2" />
                <h2 className="text-lg font-semibold text-ink">Auto-Generated Comparison</h2>
              </div>
              <div className="space-y-3">
                {comparison.metrics.map((metric, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-paper-2 rounded-lg">
                    <span className="font-medium text-ink">{metric.metric}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-ink/60">Your: {metric.your_value.toFixed(2)}</span>
                      <span className="text-sm text-ink/60">Benchmark: {metric.benchmark_value.toFixed(2)}</span>
                      <div className="flex items-center gap-1">
                        {getVarianceIcon(metric.status)}
                        <span className={`text-sm font-semibold ${getVarianceColor(metric.status)}`}>
                          {metric.variance_percentage >= 0 ? '+' : ''}{metric.variance_percentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {loading ? (
            <div className="text-center py-12 text-ink/50">Loading benchmarks...</div>
          ) : benchmarks.length === 0 ? (
            <div className="text-center py-12 text-ink/50">
              <BarChart3 className="w-16 h-16 text-ink/30 mx-auto mb-4" />
              <p className="mb-4">No benchmarks created yet</p>
              <p className="text-sm">Add benchmarks to compare your project costs against industry standards</p>
            </div>
          ) : (
            <div className="space-y-4">
              {benchmarks.map((benchmark) => (
                <div key={benchmark.id} className="border rounded-lg p-4 hover:shadow-md transition">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-ink">{benchmark.metric_name}</h3>
                        <span className="px-2 py-1 bg-paper text-ink/60 text-xs rounded-full">
                          {benchmark.category}
                        </span>
                      </div>
                      
                      <div className="flex flex-wrap gap-4 text-sm text-ink/60 mb-3">
                        <div>
                          <span className="font-medium">Your Value:</span>{' '}
                          {benchmark.your_value} {benchmark.your_unit}
                        </div>
                        <div>
                          <span className="font-medium">Benchmark:</span>{' '}
                          {benchmark.benchmark_value} {benchmark.benchmark_unit}
                        </div>
                        {benchmark.benchmark_source && (
                          <div>
                            <span className="font-medium">Source:</span> {benchmark.benchmark_source}
                          </div>
                        )}
                      </div>
                      
                      {benchmark.variance_percentage !== null && (
                        <div className="flex items-center gap-2">
                          {getVarianceIcon(benchmark.variance_status)}
                          <span className={`text-sm font-semibold ${getVarianceColor(benchmark.variance_status)}`}>
                            {benchmark.variance_percentage >= 0 ? '+' : ''}{benchmark.variance_percentage.toFixed(1)}% variance
                          </span>
                          {benchmark.variance_status === 'within_range' && (
                            <span className="text-xs text-ink/50">(within 10% of benchmark)</span>
                          )}
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => handleDelete(benchmark.id)}
                      className="p-2 hover:bg-red-50 rounded-lg"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
