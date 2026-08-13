import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth, useUser } from '@clerk/clerk-react'
import { projectsApi, blueprintFilesApi, analyticsApi, type DashboardStats, type ActivityItem } from '@/lib/api'
import { Plus, FolderOpen, Calendar, MapPin, Building2, FileText, X, Eye, GitCompare, Share2, BarChart3, Trash2, Clock, DollarSign, PieChart, TrendingUp, MessageSquare, CheckCircle, AlertCircle, Upload } from 'lucide-react'
import AdvancedSearch from '@/components/AdvancedSearch'
import BreadcrumbNav from '@/components/BreadcrumbNav'
import { useNavigationStore } from '@/stores/useNavigationStore'
import Blueprint3DBackground from '@/components/Blueprint3DBackground'
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
}

export default function Dashboard() {
  const navigate = useNavigate()
  const location = useLocation()
  const { isLoaded, isSignedIn } = useAuth()
  const { user } = useUser()
  const { setCurrentAnalysis } = useNavigationStore()
  const [projects, setProjects] = useState<Project[]>([])
  const [recentFiles, setRecentFiles] = useState<BlueprintFile[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [activities, setActivities] = useState<ActivityItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedFileForBoq, setSelectedFileForBoq] = useState<BlueprintFile | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<{ type: 'project' | 'file', id: string, name: string } | null>(null)
  const [newProject, setNewProject] = useState({
    name: '',
    code: '',
    client_name: '',
    location_city: '',
    location_state: '',
    building_type: 'residential',
  })

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      loadData()
    }
  }, [isLoaded, isSignedIn])

  // Refresh data when component mounts (user navigates back)
  useEffect(() => {
    if (isLoaded && isSignedIn) {
      loadData()
    }
  }, [location.pathname, location.key]) // Refresh on navigation changes and back/forward

  const loadData = async () => {
    try {
      setLoading(true)
      const [projectsResult, filesResult, statsResult, activityResult] = await Promise.allSettled([
        projectsApi.list(),
        blueprintFilesApi.list(undefined, 50),
        analyticsApi.getDashboardStats(),
        analyticsApi.getActivity(8),
      ])

      if (projectsResult.status === 'fulfilled') {
        setProjects(Array.isArray(projectsResult.value) ? projectsResult.value : [])
      } else {
        console.error('Failed to load projects:', projectsResult.reason)
        setProjects([])
      }

      if (filesResult.status === 'fulfilled') {
        setRecentFiles(Array.isArray(filesResult.value) ? filesResult.value : [])
      } else {
        console.error('Failed to load files:', filesResult.reason)
        setRecentFiles([])
      }

      if (statsResult.status === 'fulfilled') {
        setStats(statsResult.value)
      } else {
        console.error('Failed to load dashboard stats:', statsResult.reason)
        setStats(null)
      }

      if (activityResult.status === 'fulfilled') {
        setActivities(activityResult.value.activities || [])
      } else {
        console.error('Failed to load activity:', activityResult.reason)
        setActivities([])
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const displayName = user?.firstName || user?.fullName || user?.username || 'there'

  const projectChart = useMemo(() => {
    const series = stats?.projects_by_month || []
    const max = Math.max(1, ...series.map((s) => s.count))
    return series.map((s) => ({
      label: s.month.split(' ')[0],
      count: s.count,
      heightPct: Math.round((s.count / max) * 100),
    }))
  }, [stats])

  const materialUsage = useMemo(() => {
    const totals = new Map<string, number>()
    recentFiles.forEach((file) => {
      const materials = file.analysis_result?.materials
      if (materials && typeof materials === 'object') {
        Object.entries(materials).forEach(([name, value]) => {
          const num = typeof value === 'number' ? value : Number(value) || 0
          totals.set(name, (totals.get(name) || 0) + num)
        })
      }
      file.analysis_result?.boq?.forEach((item: any) => {
        const name = item.material_name || item.category || item.item
        const qty = Number(item.quantity) || 0
        if (name && qty > 0) totals.set(name, (totals.get(name) || 0) + qty)
      })
    })
    return [...totals.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, value]) => ({ name, value }))
  }, [recentFiles])

  const maxMaterial = Math.max(1, ...materialUsage.map((m) => m.value))

  const estimateFileCost = (file?: BlueprintFile | null) => {
    if (!file) return null
    if (file.analysis_result?.costs?.['Total Estimated Cost'] != null) {
      return Number(file.analysis_result.costs['Total Estimated Cost'])
    }
    if (file.analysis_result?.total_cost != null) return Number(file.analysis_result.total_cost)
    if (Array.isArray(file.analysis_result?.boq)) {
      const sum = file.analysis_result.boq.reduce(
        (acc: number, item: any) => acc + (Number(item.amount) || 0),
        0
      )
      return sum > 0 ? sum : null
    }
    return null
  }

  const handleCreateProject = async () => {
    console.log('handleCreateProject called')
    console.log('newProject.name:', newProject.name)

    if (!newProject.name || newProject.name.trim() === '') {
      alert('Please enter a project name')
      return
    }

    try {
      console.log('Creating project with data:', newProject)

      const createdProject = await projectsApi.create(newProject)

      console.log('Project created successfully:', createdProject)
      setShowCreateModal(false)
      setNewProject({
        name: '',
        code: '',
        client_name: '',
        location_city: '',
        location_state: '',
        building_type: 'residential',
      })
      // Re-fetch full list so shape matches the dashboard ProjectResponse type
      await loadData()
    } catch (error) {
      console.error('Failed to create project:', error)
      alert(`Failed to create project: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  const handleDeleteProject = async (id: string) => {
    try {
      await projectsApi.delete(id)
      setProjects(projects.filter(p => p.id !== id))
      setDeleteConfirm(null)
    } catch (error) {
      console.error('Failed to delete project:', error)
      alert(`Failed to delete project: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  const handleDeleteFile = async (id: string) => {
    try {
      console.log('Attempting to delete file:', id)
      const response = await blueprintFilesApi.delete(id)
      console.log('Delete response:', response)
      setRecentFiles(recentFiles.filter(f => f.id !== id))
      setDeleteConfirm(null)
    } catch (error) {
      console.error('Failed to delete file:', error)
      console.error('Error details:', error instanceof Error ? error.stack : 'No stack trace')
      alert(`Failed to delete file: ${error instanceof Error ? error.message : 'Unknown error'}`)
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
        <div className="text-ink/50">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-paper">

      <Blueprint3DBackground />

    <div className="relative z-10">
      {/* Breadcrumb Navigation */}
      <BreadcrumbNav />

      {/* Header */}
      <header className="bg-paper border-b border-ink/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-ink">Dashboard</h1>
            </div>
            <button
              onClick={() => {
                setCurrentAnalysis(null)
                navigate('/upload')
              }}
              className="flex items-center gap-2 bg-accent text-paper px-4 py-2 rounded-lg hover:bg-accent/90"
            >
              <Plus className="w-4 h-4" />
              Upload Blueprint
            </button>
          </div>
        </div>
      </header>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Bar */}
        <div className="mb-8">
          <AdvancedSearch
            onSearch={(results) => console.log('Search results:', results)}
            placeholder="Search projects, blueprints..."
          />
        </div>

        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-ink mb-2">Welcome back, {displayName} 👋</h2>
          <p className="text-ink/60">Here's what's happening with your projects today.</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-paper rounded-lg p-5 border border-ink/20 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-ink/50 uppercase tracking-wider">Total Projects</p>
                <p className="text-2xl font-bold text-ink mt-1">{stats?.total_projects ?? projects.length}</p>
                <p className="text-xs text-ink/50 mt-1">
                  {stats?.trends.projects_this_month
                    ? `+${stats.trends.projects_this_month} this month`
                    : 'No new projects this month'}
                </p>
              </div>
              <FolderOpen className="w-7 h-7 text-accent bg-accent/10 p-1.5 rounded-lg" />
            </div>
          </div>
          <div className="bg-paper rounded-lg p-5 border border-ink/20 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-ink/50 uppercase tracking-wider">Blueprints Analyzed</p>
                <p className="text-2xl font-bold text-ink mt-1">{stats?.analyses_run ?? 0}</p>
                <p className="text-xs text-ink/50 mt-1">
                  {stats?.trends.analyses_this_month
                    ? `+${stats.trends.analyses_this_month} this month`
                    : 'No analyses this month'}
                </p>
              </div>
              <FileText className="w-7 h-7 text-purple-500 bg-purple-500/10 p-1.5 rounded-lg" />
            </div>
          </div>
          <div className="bg-paper rounded-lg p-5 border border-ink/20 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-ink/50 uppercase tracking-wider">Estimated Cost</p>
                <p className="text-2xl font-bold text-ink mt-1">
                  {formatInrCompact(stats?.total_estimated_value ?? 0)}
                </p>
                <p className="text-xs text-ink/50 mt-1">Across your projects</p>
              </div>
              <DollarSign className="w-7 h-7 text-teal-500 bg-teal-500/10 p-1.5 rounded-lg" />
            </div>
          </div>
          <div className="bg-paper rounded-lg p-5 border border-ink/20 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-ink/50 uppercase tracking-wider">Avg. Analysis Time</p>
                <p className="text-2xl font-bold text-ink mt-1">
                  {stats?.avg_analysis_seconds != null ? `${stats.avg_analysis_seconds} sec` : '—'}
                </p>
                <p className="text-xs text-ink/50 mt-1">Per blueprint</p>
              </div>
              <Clock className="w-7 h-7 text-yellow-600 bg-yellow-600/10 p-1.5 rounded-lg" />
            </div>
          </div>
        </div>


        {/* Main Grid - Projects & Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Recent Projects */}
          <div className="lg:col-span-2">
            {/* Recent Projects Table */}
            <div className="bg-paper/80 backdrop-blur-sm rounded-lg border border-ink/20 shadow-sm mb-8">
              <div className="px-5 py-4 border-b border-ink/15 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-ink uppercase tracking-wider">Recent Projects</h2>
                <button
                  onClick={() => navigate('/projects')}
                  className="text-accent hover:text-accent/80 text-sm font-medium flex items-center"
                >
                  View All Projects →
                </button>
              </div>
              {projects.length === 0 ? (
                <div className="p-12 text-center">
                  <FolderOpen className="w-12 h-12 text-ink/40 mx-auto mb-4" />
                  <p className="text-ink/50 mb-4">No projects yet</p>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="bg-accent text-paper px-4 py-2 rounded-lg hover:bg-accent/90"
                  >
                    Create your first project
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-paper-2">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">Project Name</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">Blueprint</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">Area</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">Estimated Cost</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">Last Updated</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink/10">
                      {projects.slice(0, 4).map((project) => {
                        const projectFile = recentFiles.find(f => f.project_id === project.id)
                        return (
                          <tr key={project.id} className="hover:bg-paper-2">
                            <td className="px-6 py-4">
                              <div className="flex items-center">
                                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent/20 to-accent/10 border border-accent/20 flex items-center justify-center mr-3">
                                  <FolderOpen className="w-5 h-5 text-accent" />
                                </div>
                                <div className="font-medium text-ink text-sm">{project.name}</div>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${project.status === 'active' ? 'bg-green-500/10 text-green-500' :
                                project.status === 'completed' ? 'bg-accent/10 text-accent' :
                                  project.status === 'draft' ? 'bg-ink/10 text-ink/60' :
                                    'bg-yellow-500/10 text-yellow-500'
                                }`}>
                                <div className={`w-1.5 h-1.5 rounded-full inline-block mr-1 ${project.status === 'active' ? 'bg-green-500' :
                                  project.status === 'completed' ? 'bg-accent' :
                                    project.status === 'draft' ? 'bg-ink/60' :
                                      'bg-yellow-500'
                                  }`}></div>
                                {project.status.charAt(0).toUpperCase() + project.status.slice(1)}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              {projectFile ? (
                                <button
                                  onClick={() => {
                                    setCurrentAnalysis({ fileId: projectFile.id, projectId: project.id, fileName: projectFile.filename, originPath: `/results/${projectFile.id}` })
                                    navigate(`/results/${projectFile.id}`)
                                  }}
                                  className="flex items-center text-accent hover:text-accent/80 text-sm transition-colors"
                                >
                                  <FileText className="w-4 h-4 mr-1" />
                                  {projectFile.filename}
                                </button>
                              ) : (
                                <div className="flex items-center text-ink/40 text-sm">
                                  <FileText className="w-4 h-4 mr-1" />
                                  No file yet
                                </div>
                              )}
                            </td>
                            <td className="px-6 py-4 text-ink/70 text-sm">
                              {projectFile?.total_area ? `${projectFile.total_area} sq ft` : '—'}
                            </td>
                            <td className="px-6 py-4 text-ink/70 text-sm">
                              {formatInr(estimateFileCost(projectFile) ?? undefined)}
                            </td>
                            <td className="px-6 py-4 text-ink/70 text-sm">
                              {new Date(project.created_at).toLocaleDateString('en-IN')}
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={() => navigate(`/upload?project=${project.id}`)}
                                  title="Upload blueprint for this project"
                                  className="flex items-center gap-1 text-xs text-accent hover:text-accent/80 border border-accent/20 rounded-full px-2 py-1 hover:bg-accent/5 transition"
                                >
                                  <Upload className="w-3 h-3" />
                                  Upload
                                </button>
                                {projectFile && (
                                  <button
                                    onClick={() => {
                                      setCurrentAnalysis({ fileId: projectFile.id, projectId: project.id, fileName: projectFile.filename, originPath: `/results/${projectFile.id}` })
                                      navigate(`/results/${projectFile.id}`)
                                    }}
                                    title="View analysis results"
                                    className="flex items-center gap-1 text-xs text-ink/60 hover:text-ink border border-ink/15 rounded-full px-2 py-1 hover:bg-paper-2 transition"
                                  >
                                    <Eye className="w-3 h-3" />
                                    Results
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-2 gap-6">
              {/* Projects Overview Chart */}
              <div className="bg-paper/70 backdrop-blur-md rounded-lg border border-ink/20 shadow-sm p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-ink uppercase tracking-wider">Projects Overview</h3>
                  <span className="text-xs text-ink/50">Last 6 months</span>
                </div>
                {projectChart.every((b) => b.count === 0) ? (
                  <div className="h-48 flex items-center justify-center text-sm text-ink/50">
                    No project activity yet
                  </div>
                ) : (
                  <div className="h-48 flex items-end justify-around gap-2">
                    {projectChart.map((bar) => (
                      <div key={bar.label} className="flex flex-col items-center flex-1">
                        <div
                          className="w-full bg-gradient-to-t from-accent to-accent/60 rounded-t min-h-[4px]"
                          style={{ height: `${Math.max(bar.heightPct, bar.count > 0 ? 8 : 0)}%` }}
                          title={`${bar.count} project(s)`}
                        ></div>
                        <span className="text-xs text-ink/50 mt-2">{bar.label}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Material Usage Chart */}
              <div className="bg-paper/70 backdrop-blur-md rounded-lg border border-ink/20 shadow-sm p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-ink uppercase tracking-wider">Material Usage</h3>
                </div>
                {materialUsage.length === 0 ? (
                  <div className="h-48 flex items-center justify-center text-sm text-ink/50">
                    No material data from your analyses yet
                  </div>
                ) : (
                  <div className="space-y-3">
                    {materialUsage.map((item) => (
                      <div key={item.name}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-ink/70">{item.name}</span>
                          <span className="font-medium text-cyan-500">{item.value.toLocaleString()}</span>
                        </div>
                        <div className="w-full h-2 bg-ink/10 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-cyan-500 rounded-full"
                            style={{ width: `${(item.value / maxMaterial) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - AI Assistant & Recent Activity */}
          <div className="lg:col-span-1 space-y-6">
            {/* AI Assistant */}
            <div className="bg-paper/70 backdrop-blur-md rounded-lg border border-ink/20 shadow-sm p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-ink uppercase tracking-wider">AI Assistant</h3>
                <span className="text-xs font-medium bg-purple-500/20 text-purple-500 px-2 py-0.5 rounded">BETA</span>
              </div>
              <p className="text-xs text-ink/60 mb-4">Ask anything about your blueprints</p>
              <div className="space-y-2 mb-4">
                {[
                  'Which room is the largest?',
                  'How much cement is required?',
                  'Generate BOQ for this project',
                  'Suggest cost optimization ideas'
                ].map((question, i) => (
                  <button
                    key={i}
                    className="w-full text-left text-xs bg-paper-2 hover:bg-paper-2/80 border border-ink/15 rounded px-3 py-2 text-ink/70 transition"
                  >
                    <MessageSquare className="w-3 h-3 inline mr-2" />
                    {question}
                  </button>
                ))}
              </div>
              <button
                onClick={() => navigate('/ai-assistant')}
                className="w-full text-accent hover:text-accent/80 text-xs font-medium flex items-center justify-center gap-1 py-2 border border-accent/20 rounded hover:bg-accent/5 transition"
              >
                Open AI Assistant →
              </button>
            </div>

            {/* Recent Activity */}
            <div className="bg-paper/70 backdrop-blur-md rounded-lg border border-ink/20 shadow-sm p-5">
              <h3 className="text-sm font-semibold text-ink uppercase tracking-wider mb-4">Recent Activity</h3>
              {activities.length === 0 ? (
                <p className="text-xs text-ink/50 py-4 text-center">No recent activity yet. Upload a blueprint to get started.</p>
              ) : (
                <div className="space-y-3">
                  {activities.map((activity) => {
                    const isFail = activity.event_type === 'analysis_failed'
                    const isUpload = activity.event_type === 'file_uploaded'
                    const Icon = isFail ? AlertCircle : isUpload ? Upload : CheckCircle
                    const color = isFail ? 'text-red-500' : isUpload ? 'text-blue-500' : 'text-green-500'
                    const bg = isFail ? 'bg-red-500/10' : isUpload ? 'bg-blue-500/10' : 'bg-green-500/10'
                    return (
                      <div key={activity.id} className="flex gap-3">
                        <div className={`${bg} p-2 rounded-lg flex-shrink-0`}>
                          <Icon className={`w-4 h-4 ${color}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-ink">{activity.description}</p>
                          <p className="text-xs text-ink/50">{activity.formatted_time || activity.created_at}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-paper rounded-xl p-6 w-full max-w-md mx-4 border border-ink/10">
            <h2 className="text-xl font-bold text-ink mb-4">Create New Project</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Project Name *</label>
                <input
                  type="text"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
                  placeholder="Enter project name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Project Code</label>
                <input
                  type="text"
                  value={newProject.code}
                  onChange={(e) => setNewProject({ ...newProject, code: e.target.value })}
                  className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
                  placeholder="Enter project code"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Client Name</label>
                <input
                  type="text"
                  value={newProject.client_name}
                  onChange={(e) => setNewProject({ ...newProject, client_name: e.target.value })}
                  className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
                  placeholder="Enter client name"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">City</label>
                  <input
                    type="text"
                    value={newProject.location_city}
                    onChange={(e) => setNewProject({ ...newProject, location_city: e.target.value })}
                    className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
                    placeholder="City"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">State</label>
                  <input
                    type="text"
                    value={newProject.location_state}
                    onChange={(e) => setNewProject({ ...newProject, location_state: e.target.value })}
                    className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
                    placeholder="State"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Building Type</label>
                <select
                  value={newProject.building_type}
                  onChange={(e) => setNewProject({ ...newProject, building_type: e.target.value })}
                  className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
                >
                  <option value="residential">Residential</option>
                  <option value="commercial">Commercial</option>
                  <option value="industrial">Industrial</option>
                  <option value="mixed_use">Mixed Use</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 border border-ink/15 rounded-lg hover:bg-paper-2"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateProject}
                disabled={!newProject.name}
                className="px-4 py-2 bg-accent text-paper rounded-lg hover:bg-accent/90 disabled:bg-ink/20"
              >
                Create Project
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BOQ View Modal */}
      {selectedFileForBoq && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-paper rounded-xl max-w-4xl w-full max-h-[80vh] overflow-hidden border border-ink/10">
            <div className="px-6 py-4 border-b border-ink/10 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-ink">
                BOQ: {selectedFileForBoq.filename}
              </h2>
              <button
                onClick={() => setSelectedFileForBoq(null)}
                className="text-ink/40 hover:text-ink/60"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {selectedFileForBoq.analysis_result?.boq ? (
                <div className="overflow-hidden rounded-lg border border-ink/10">
                  <table className="w-full">
                    <thead className="bg-paper-2">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                          Item
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-ink/60 uppercase">
                          Qty
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-ink/60 uppercase">
                          Unit
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-ink/60 uppercase">
                          Amount
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink/10">
                      {selectedFileForBoq.analysis_result.boq.map((b: any, idx: number) => (
                        <tr key={idx} className="bg-paper">
                          <td className="px-4 py-3 text-sm font-medium text-ink">
                            {b.item ?? `Item ${idx + 1}`}
                          </td>
                          <td className="px-4 py-3 text-sm text-right text-ink/70">
                            {b.quantity ?? '—'}
                          </td>
                          <td className="px-4 py-3 text-sm text-right text-ink/70">
                            {b.unit ?? ''}
                          </td>
                          <td className="px-4 py-3 text-sm text-right text-ink/70">
                            {formatInr(b.amount)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-paper-2">
                      <tr>
                        <td colSpan={3} className="px-4 py-3 text-sm font-medium text-ink text-right">
                          Total:
                        </td>
                        <td className="px-4 py-3 text-sm font-medium text-ink text-right">
                          {formatInr(
                            selectedFileForBoq.analysis_result.boq.reduce(
                              (sum: number, item: any) => sum + (item.amount || 0),
                              0
                            )
                          )}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No BOQ data available for this file
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-paper rounded-xl p-6 w-full max-w-md mx-4 border border-ink/10">
            <h2 className="text-xl font-bold text-ink mb-4">
              Delete {deleteConfirm.type === 'project' ? 'Project' : 'File'}?
            </h2>
            <p className="text-ink/70 mb-6">
              Are you sure you want to delete "{deleteConfirm.name}"? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 border border-ink/15 rounded-lg hover:bg-paper-2"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (deleteConfirm.type === 'project') {
                    handleDeleteProject(deleteConfirm.id)
                  } else {
                    handleDeleteFile(deleteConfirm.id)
                  }
                }}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function formatInr(value?: number) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatInrCompact(value?: number) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) return '—'
  if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)} Cr`
  if (value >= 100000) return `₹${(value / 100000).toFixed(1)} L`
  return formatInr(value)
}
