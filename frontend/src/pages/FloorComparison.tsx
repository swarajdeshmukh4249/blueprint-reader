import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { floorComparisonApi, blueprintFilesApi, projectsApi } from '../lib/api'
import { ArrowLeft, Layers, GitCompare, Eye, AlertCircle } from 'lucide-react'

type ViewMode = 'side-by-side' | 'overlay' | 'diff-only'

interface RoomDiff {
  room_name: string
  room_type: string
  status: string
  area_a: number | null
  area_b: number | null
  area_delta: number | null
  dims_a: [number, number] | null
  dims_b: [number, number] | null
  match_confidence: number
}

interface FloorComparison {
  id: string
  project_id: string
  floor_a_id: string | null
  floor_b_id: string | null
  floor_a_label: string | null
  floor_b_label: string | null
  total_area_a: number | null
  total_area_b: number | null
  area_delta: number | null
  boq_cost_a: number | null
  boq_cost_b: number | null
  cost_delta: number | null
  room_diffs: RoomDiff[]
  comparison_type: string
  created_at: string
}

interface BlueprintFile {
  id: string
  filename: string
  project_id: string | null
  status: string
  total_area: number | null
  room_count: number | null
  created_at: string
  analyzed_at: string | null
  analysis_result: any
}

export default function FloorComparison() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  
  const [comparison, setComparison] = useState<FloorComparison | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('side-by-side')
  
  // For creating new comparison
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [files, setFiles] = useState<BlueprintFile[]>([])
  const [selectedFileA, setSelectedFileA] = useState<string>('')
  const [selectedFileB, setSelectedFileB] = useState<string>('')
  const [floorALabel, setFloorALabel] = useState('Floor A')
  const [floorBLabel, setFloorBLabel] = useState('Floor B')

  useEffect(() => {
    loadFiles()
  }, [projectId])

  const loadFiles = async () => {
    try {
      const data: BlueprintFile[] = await blueprintFilesApi.list(projectId, 50)
      console.log('Loaded files for comparison:', data)
      setFiles(data.filter(f => f.status === 'analyzed'))
    } catch (err) {
      console.error('Failed to load files:', err)
    }
  }

  const handleCreateComparison = async () => {
    if (!selectedFileA || !selectedFileB) {
      setError('Please select both files to compare')
      return
    }

    if (selectedFileA === selectedFileB) {
      setError('Please select different files to compare')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result: FloorComparison = await floorComparisonApi.compare({
        project_id: projectId!,
        file_a_id: selectedFileA,
        file_b_id: selectedFileB,
        floor_a_label: floorALabel,
        floor_b_label: floorBLabel,
      })
      setComparison(result)
      setShowCreateForm(false)
    } catch (err: any) {
      setError(err.message || 'Failed to create comparison')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value: number | null) => {
    if (value === null) return '—'
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'match': return 'bg-green-100 text-green-800'
      case 'changed': return 'bg-yellow-100 text-yellow-800'
      case 'added': return 'bg-blue-100 text-blue-800'
      case 'removed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  // Edge case: Not enough files to compare
  if (!showCreateForm && !comparison && files.length < 2) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back
          </button>

          <div className="bg-white rounded-xl border p-12 text-center">
            <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Not Enough Analyzed Files
            </h2>
            <p className="text-gray-600 mb-6">
              You need at least 2 analyzed blueprint files to compare floors.
              Upload and analyze more files to use this feature.
            </p>
            <button
              onClick={() => navigate('/upload')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Upload New File
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back
        </button>

        {!showCreateForm && !comparison && (
          <div className="bg-white rounded-xl border p-8">
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-2xl font-bold text-gray-900">Floor Comparison</h1>
              <button
                onClick={() => setShowCreateForm(true)}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <GitCompare className="w-4 h-4 mr-2" />
                New Comparison
              </button>
            </div>

            <p className="text-gray-600 mb-6">
              Compare two analyzed blueprint files to see differences in rooms, areas, and BOQ costs.
            </p>

            {files.length >= 2 && (
              <div className="text-sm text-gray-500">
                {files.length} analyzed files available for comparison
              </div>
            )}
          </div>
        )}

        {showCreateForm && (
          <div className="bg-white rounded-xl border p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Create New Comparison</h2>

            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Floor A (First File)
                </label>
                <select
                  value={selectedFileA}
                  onChange={(e) => setSelectedFileA(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">Select file...</option>
                  {files.map((file) => (
                    <option key={file.id} value={file.id}>
                      {file.filename} ({file.total_area || 0} sq ft)
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  value={floorALabel}
                  onChange={(e) => setFloorALabel(e.target.value)}
                  placeholder="Floor A"
                  className="mt-2 w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Floor B (Second File)
                </label>
                <select
                  value={selectedFileB}
                  onChange={(e) => setSelectedFileB(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">Select file...</option>
                  {files.map((file) => (
                    <option key={file.id} value={file.id}>
                      {file.filename} ({file.total_area || 0} sq ft)
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  value={floorBLabel}
                  onChange={(e) => setFloorBLabel(e.target.value)}
                  placeholder="Floor B"
                  className="mt-2 w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <div className="mt-6 flex gap-3">
              <button
                onClick={handleCreateComparison}
                disabled={loading || !selectedFileA || !selectedFileB}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
              >
                {loading ? 'Comparing...' : 'Compare Floors'}
              </button>
              <button
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {comparison && (
          <div className="space-y-6">
            {/* Header */}
            <div className="bg-white rounded-xl border p-6">
              <div className="flex items-center justify-between mb-4">
                <h1 className="text-2xl font-bold text-gray-900">Floor Comparison Results</h1>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50 text-sm"
                >
                  New Comparison
                </button>
              </div>

              {/* Summary Cards */}
              <div className="grid gap-4 md:grid-cols-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Total Area A</div>
                  <div className="text-xl font-semibold text-gray-900">
                    {comparison.total_area_a ? `${comparison.total_area_a} sq ft` : '—'}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Total Area B</div>
                  <div className="text-xl font-semibold text-gray-900">
                    {comparison.total_area_b ? `${comparison.total_area_b} sq ft` : '—'}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Area Delta</div>
                  <div className={`text-xl font-semibold ${comparison.area_delta && comparison.area_delta > 0 ? 'text-green-600' : comparison.area_delta && comparison.area_delta < 0 ? 'text-red-600' : 'text-gray-900'}`}>
                    {comparison.area_delta !== null ? `${comparison.area_delta > 0 ? '+' : ''}${comparison.area_delta} sq ft` : '—'}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Cost Delta</div>
                  <div className={`text-xl font-semibold ${comparison.cost_delta && comparison.cost_delta > 0 ? 'text-green-600' : comparison.cost_delta && comparison.cost_delta < 0 ? 'text-red-600' : 'text-gray-900'}`}>
                    {comparison.cost_delta !== null ? formatCurrency(comparison.cost_delta) : '—'}
                  </div>
                </div>
              </div>

              {/* View Mode Toggle */}
              <div className="flex items-center gap-2 mb-4">
                <span className="text-sm text-gray-600">View Mode:</span>
                <button
                  onClick={() => setViewMode('side-by-side')}
                  className={`px-3 py-1 rounded text-sm ${viewMode === 'side-by-side' ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200'}`}
                >
                  Side by Side
                </button>
                <button
                  onClick={() => setViewMode('overlay')}
                  className={`px-3 py-1 rounded text-sm ${viewMode === 'overlay' ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200'}`}
                >
                  Overlay
                </button>
                <button
                  onClick={() => setViewMode('diff-only')}
                  className={`px-3 py-1 rounded text-sm ${viewMode === 'diff-only' ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200'}`}
                >
                  Diff Only
                </button>
              </div>
            </div>

            {/* Room Diff Table */}
            <div className="bg-white rounded-xl border">
              <div className="px-6 py-4 border-b">
                <h2 className="text-lg font-semibold text-gray-900">Room Differences</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Room Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Status
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        Area A
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        Area B
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        Delta
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        Confidence
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {comparison.room_diffs
                      .filter(diff => viewMode === 'diff-only' ? diff.status !== 'match' : true)
                      .map((diff, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-6 py-4 font-medium text-gray-900">
                            {diff.room_name}
                          </td>
                          <td className="px-6 py-4 text-gray-600">
                            {diff.room_type}
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(diff.status)}`}>
                              {diff.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right text-gray-600">
                            {diff.area_a ? `${diff.area_a} sq ft` : '—'}
                          </td>
                          <td className="px-6 py-4 text-right text-gray-600">
                            {diff.area_b ? `${diff.area_b} sq ft` : '—'}
                          </td>
                          <td className={`px-6 py-4 text-right font-medium ${diff.area_delta && diff.area_delta > 0 ? 'text-green-600' : diff.area_delta && diff.area_delta < 0 ? 'text-red-600' : 'text-gray-900'}`}>
                            {diff.area_delta !== null ? `${diff.area_delta > 0 ? '+' : ''}${diff.area_delta} sq ft` : '—'}
                          </td>
                          <td className={`px-6 py-4 text-right text-sm ${getConfidenceColor(diff.match_confidence)}`}>
                            {diff.match_confidence > 0 ? `${Math.round(diff.match_confidence * 100)}%` : '—'}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
