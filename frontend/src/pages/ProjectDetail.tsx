import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import { projectsApi, blueprintFilesApi } from '@/lib/api'
import { ArrowLeft, Upload, FileText, Eye, BarChart3, GitCompare, Share2, Plus, Trash2, RefreshCw } from 'lucide-react'

interface Project {
  id: string
  name: string
  code?: string
  client_name?: string
  location_city?: string
  location_state?: string
  building_type?: string
  status: string
  created_at: string
  updated_at?: string
}

interface BlueprintFile {
  id: string
  filename: string
  project_id?: string
  status: string
  total_area?: number
  room_count?: number
  created_at: string
  analyzed_at?: string
  analysis_result?: any
  file_path?: string
}

export default function ProjectDetail() {
  const navigate = useNavigate()
  const { projectId } = useParams<{ projectId: string }>()
  const { isLoaded, isSignedIn } = useAuth()
  const [project, setProject] = useState<Project | null>(null)
  const [files, setFiles] = useState<BlueprintFile[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState<string | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  useEffect(() => {
    if (isLoaded && isSignedIn && projectId) {
      loadProjectData()
    }
  }, [isLoaded, isSignedIn, projectId])

  const loadProjectData = async () => {
    try {
      setLoading(true)
      const [projectData, filesData] = await Promise.all([
        projectsApi.get(projectId!),
        blueprintFilesApi.list(projectId),
      ])
      setProject(projectData)
      setFiles(filesData)
    } catch (error) {
      console.error('Failed to load project data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile || !projectId) return

    try {
      setUploading(true)
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('project_id', projectId)

      await blueprintFilesApi.create(formData)
      setShowUploadModal(false)
      setSelectedFile(null)
      loadProjectData()
    } catch (error) {
      console.error('Failed to upload file:', error)
      alert('Failed to upload file')
    } finally {
      setUploading(false)
    }
  }

  const handleAnalyze = async (fileId: string) => {
    try {
      setAnalyzing(fileId)
      await blueprintFilesApi.analyze(fileId)
      loadProjectData()
    } catch (error) {
      console.error('Failed to analyze file:', error)
      alert('Failed to analyze file')
    } finally {
      setAnalyzing(null)
    }
  }

  const handleDelete = async (fileId: string) => {
    if (!confirm('Are you sure you want to delete this file?')) return

    try {
      await blueprintFilesApi.delete(fileId)
      loadProjectData()
    } catch (error) {
      console.error('Failed to delete file:', error)
      alert('Failed to delete file')
    }
  }

  if (!isLoaded || !isSignedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-ink/50">Loading...</div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-ink/50">Loading project...</div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-ink/50">Project not found</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-ink/5">
      {/* Header */}
      <header className="bg-paper-2 border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-ink/60 hover:text-ink"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl font-bold text-ink">{project.name}</h1>
                {project.code && (
                  <p className="text-sm text-ink/50">{project.code}</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3">
              {files.length >= 2 && (
                <button
                  onClick={() => navigate(`/floor-comparison/${projectId}`)}
                  className="flex items-center gap-2 border border-ink/20 px-3 py-2 rounded-lg hover:bg-ink/5 text-sm"
                >
                  <GitCompare className="w-4 h-4" />
                  Compare Floors
                </button>
              )}
              {files.length >= 1 && (
                <button
                  onClick={() => navigate(`/public-share/${projectId}`)}
                  className="flex items-center gap-2 border border-ink/20 px-3 py-2 rounded-lg hover:bg-ink/5 text-sm"
                >
                  <Share2 className="w-4 h-4" />
                  Share
                </button>
              )}
              {files.length >= 1 && (
                <button
                  onClick={() => navigate(`/cost-benchmarking/${projectId}`)}
                  className="flex items-center gap-2 border border-ink/20 px-3 py-2 rounded-lg hover:bg-ink/5 text-sm"
                >
                  <BarChart3 className="w-4 h-4" />
                  Benchmark
                </button>
              )}
              <button
                onClick={() => setShowUploadModal(true)}
                className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                <Upload className="w-4 h-4" />
                Upload Blueprint
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Project Info */}
        <div className="bg-paper-2 rounded-xl border p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-ink/50">Client</p>
              <p className="font-medium text-ink">{project.client_name || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-ink/50">Location</p>
              <p className="font-medium text-ink">
                {project.location_city && project.location_state
                  ? `${project.location_city}, ${project.location_state}`
                  : '-'}
              </p>
            </div>
            <div>
              <p className="text-sm text-ink/50">Building Type</p>
              <p className="font-medium text-ink">{project.building_type || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-ink/50">Status</p>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                project.status === 'active' ? 'bg-green-100 text-green-800' :
                project.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                project.status === 'draft' ? 'bg-paper text-ink' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {project.status}
              </span>
            </div>
          </div>
        </div>

        {/* Blueprint Files */}
        <div className="bg-paper-2 rounded-xl border">
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <h2 className="text-lg font-semibold text-ink">Blueprint Files</h2>
            <span className="text-sm text-ink/50">{files.length} files</span>
          </div>
          {files.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 text-ink/40 mx-auto mb-4" />
              <p className="text-ink/50 mb-4">No blueprints uploaded yet</p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                Upload your first blueprint
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-ink/5">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/50 uppercase">
                      File
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/50 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/50 uppercase">
                      Area
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/50 uppercase">
                      Rooms
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/50 uppercase">
                      Analyzed
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/50 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {files.map((file) => (
                    <tr key={file.id} className="hover:bg-ink/5">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <FileText className="w-5 h-5 text-ink/40 mr-3" />
                          <div className="font-medium text-ink">{file.filename}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          file.status === 'analyzed' ? 'bg-green-100 text-green-800' :
                          file.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-paper text-ink'
                        }`}>
                          {file.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-ink/60">
                        {file.total_area ? `${file.total_area} sq ft` : '-'}
                      </td>
                      <td className="px-6 py-4 text-ink/60">
                        {file.room_count || '-'}
                      </td>
                      <td className="px-6 py-4 text-ink/60 text-sm">
                        {file.analyzed_at ? new Date(file.analyzed_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          {file.status === 'uploaded' && (
                            <button
                              onClick={() => handleAnalyze(file.id)}
                              disabled={analyzing === file.id}
                              className="text-blue-600 hover:text-blue-700 text-sm font-medium disabled:opacity-50"
                            >
                              {analyzing === file.id ? (
                                <RefreshCw className="w-4 h-4 animate-spin" />
                              ) : (
                                'Analyze'
                              )}
                            </button>
                          )}
                          {file.status === 'analyzed' && (
                            <>
                              <button
                                onClick={() => navigate(`/results/${file.id}`)}
                                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(file.id)}
                                className="text-red-600 hover:text-red-700 text-sm font-medium"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-paper-2 rounded-xl p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-bold text-ink mb-4">Upload Blueprint</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ink/80 mb-1">Select File</label>
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,.dxf,.dwg"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full border rounded-lg px-3 py-2"
                />
                <p className="text-xs text-ink/50 mt-1">
                  Supported formats: PDF, PNG, JPG, DXF, DWG (max 50MB)
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 border rounded-lg hover:bg-ink/5"
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
