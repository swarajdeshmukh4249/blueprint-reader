import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import {
  BarChart3,
  TrendingUp,
  Users,
  Share2,
  Download,
  Calendar,
  Building2,
  FileText,
  ArrowUpRight,
  ArrowDownRight,
  Filter,
  Plus,
  Eye,
  Copy,
  Mail,
  Link as LinkIcon,
  PieChart,
  Activity,
  ArrowLeft,
  LayoutDashboard,
  Upload as UploadIcon
} from 'lucide-react'
import { projectsApi, publicSharesApi } from '@/lib/api'
import { useNavigationStore } from '@/stores/useNavigationStore'

interface ShareLink {
  id: string
  project_id: string
  project_name: string
  token: string
  created_at: string
  expires_at: string
  access_count: number
  is_active: boolean
}

interface AnalyticsData {
  total_projects: number
  active_projects: number
  total_analyses: number
  total_shares: number
  recent_activity: any[]
  top_projects: any[]
}

export default function NewAnalytics() {
  const navigate = useNavigate()
  const { isLoaded, isSignedIn } = useAuth()
  const { currentAnalysis } = useNavigationStore()
  const [showShareModal, setShowShareModal] = useState(false)
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [shareExpiry, setShareExpiry] = useState('7')
  const [copiedLink, setCopiedLink] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const [analytics, setAnalytics] = useState<AnalyticsData>({
    total_projects: 0,
    active_projects: 0,
    total_analyses: 0,
    total_shares: 0,
    recent_activity: [],
    top_projects: []
  })

  const [shareLinks, setShareLinks] = useState<ShareLink[]>([])
  const [projects, setProjects] = useState<any[]>([])

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      loadData()
    }
  }, [isLoaded, isSignedIn])

  const loadData = async () => {
    try {
      setLoading(true)
      const [projectsData] = await Promise.all([
        projectsApi.list()
      ])
      setProjects(projectsData)

      // Calculate analytics from real data
      setAnalytics({
        total_projects: projectsData.length,
        active_projects: projectsData.filter((p: any) => p.status === 'active').length,
        total_analyses: projectsData.reduce((sum: number, p: any) => sum + (p.analysis_count || 0), 0),
        total_shares: shareLinks.length,
        recent_activity: [],
        top_projects: projectsData.slice(0, 5)
      })

      // Load share links for each project
      const allShareLinks: ShareLink[] = []
      for (const project of projectsData) {
        try {
          const shares = await publicSharesApi.list(project.id)
          allShareLinks.push(...shares)
        } catch (error) {
          console.error(`Failed to load shares for project ${project.id}:`, error)
        }
      }
      setShareLinks(allShareLinks)
    } catch (error) {
      console.error('Failed to load analytics data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateShareLink = async () => {
    if (!selectedProject) {
      alert('Please select a project')
      return
    }
    try {
      await publicSharesApi.create({
        blueprint_file_id: selectedProject,
        expires_in_days: parseInt(shareExpiry)
      })
      setShowShareModal(false)
      setSelectedProject('')
      loadData() // Reload data after creating share link
    } catch (error) {
      console.error('Failed to create share link:', error)
      alert('Failed to create share link')
    }
  }

  const handleCopyLink = (token: string) => {
    const link = `${window.location.origin}/share/${token}`
    navigator.clipboard.writeText(link)
    setCopiedLink(token)
    setTimeout(() => setCopiedLink(null), 2000)
  }

  const handleSendEmail = (shareLink: ShareLink) => {
    const subject = `Blueprint Analysis: ${shareLink.project_name}`
    const body = `You have been invited to view the blueprint analysis for ${shareLink.project_name}.\n\nAccess link: ${window.location.origin}/share/${shareLink.token}\n\nThis link expires on ${new Date(shareLink.expires_at).toLocaleDateString()}`
    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
  }

  if (!isLoaded || !isSignedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading analytics...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Breadcrumb navigation bar */}
      <div className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between py-3">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <button onClick={() => navigate('/dashboard')} className="flex items-center gap-1.5 hover:text-gray-900 transition-colors">
              <LayoutDashboard className="w-3.5 h-3.5" />
              Dashboard
            </button>
            <span className="text-gray-300">/</span>
            <span className="text-gray-900 font-medium">Analytics</span>
          </div>
          <div className="flex items-center gap-2">
            {currentAnalysis?.fileId && (
              <button
                onClick={() => navigate(currentAnalysis.originPath || `/results/${currentAnalysis.fileId}`)}
                className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-900 border border-gray-200 rounded-full px-3 py-1.5 transition-colors hover:bg-gray-50"
              >
                <ArrowLeft className="w-3 h-3" />
                Back to Results
              </button>
            )}
            <button
              onClick={() => navigate('/upload')}
              className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-900 border border-gray-200 rounded-full px-3 py-1.5 transition-colors hover:bg-gray-50"
            >
              <UploadIcon className="w-3 h-3" />
              Upload Blueprint
            </button>
          </div>
        </div>
      </div>

      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <BarChart3 className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Analytics & Client Portal</h1>
            </div>
            <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50">
                <Filter className="w-4 h-4" />
                Filter
              </button>
              <button className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50">
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Projects</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{analytics.total_projects}</p>
                <p className="text-xs text-green-600 mt-1 flex items-center">
                  <ArrowUpRight className="w-3 h-3 mr-1" />
                  +12% this month
                </p>
              </div>
              <Building2 className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Active Projects</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{analytics.active_projects}</p>
                <p className="text-xs text-green-600 mt-1 flex items-center">
                  <ArrowUpRight className="w-3 h-3 mr-1" />
                  +8% this month
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Analyses Run</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{analytics.total_analyses}</p>
                <p className="text-xs text-green-600 mt-1 flex items-center">
                  <ArrowUpRight className="w-3 h-3 mr-1" />
                  +25% this month
                </p>
              </div>
              <FileText className="w-8 h-8 text-yellow-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Client Shares</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{shareLinks.length}</p>
                <p className="text-xs text-gray-500 mt-1">Active links</p>
              </div>
              <Users className="w-8 h-8 text-purple-600" />
            </div>
          </div>
        </div>

        {/* Client Share Portal Section */}
        <div className="bg-white rounded-lg border border-gray-200 mb-8 shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Share2 className="w-5 h-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900">Client Share Portal</h2>
            </div>
            <button
              onClick={() => setShowShareModal(true)}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Create Share Link
            </button>
          </div>
          <div className="p-6">
            {shareLinks.length === 0 ? (
              <div className="text-center py-12">
                <Share2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 mb-4">No share links created yet</p>
                <button
                  onClick={() => setShowShareModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  Create your first share link
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Project
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Share Link
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Created
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Expires
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Access Count
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {shareLinks.map((link) => (
                      <tr key={link.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 font-medium text-gray-900">
                          {link.project_name}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600">
                              /share/{link.token}
                            </code>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-gray-600 text-sm">
                          {new Date(link.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 text-gray-600 text-sm">
                          {new Date(link.expires_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 text-gray-600">
                          {link.access_count}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${link.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                            {link.is_active ? 'Active' : 'Expired'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleCopyLink(link.token)}
                              className="text-blue-600 hover:text-blue-700"
                              title="Copy link"
                            >
                              {copiedLink === link.token ? <Copy className="w-4 h-4" /> : <LinkIcon className="w-4 h-4" />}
                            </button>
                            <button
                              onClick={() => handleSendEmail(link)}
                              className="text-blue-600 hover:text-blue-700"
                              title="Send email"
                            >
                              <Mail className="w-4 h-4" />
                            </button>
                            <button
                              className="text-blue-600 hover:text-blue-700"
                              title="View"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Project Analytics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Top Projects */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Top Projects</h2>
            </div>
            <div className="p-6">
              {projects.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No projects yet</div>
              ) : (
                projects.slice(0, 5).map((project, index) => (
                  <div key={project.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold text-sm">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{project.name}</div>
                        <div className="text-xs text-gray-500">{project.client_name || 'No client'}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">{project.status || 'Active'}</div>
                      <div className="text-xs text-gray-500">{project.location_city || 'Unknown'}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
            </div>
            <div className="p-6">
              {analytics.recent_activity.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No recent activity</div>
              ) : (
                analytics.recent_activity.map((activity: any, index: number) => (
                  <div key={index} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                    <div className="flex items-center gap-3">
                      <Activity className="w-5 h-5 text-gray-400" />
                      <div>
                        <div className="font-medium text-gray-900 text-sm">{activity.action}</div>
                        <div className="text-xs text-gray-500">{activity.project}</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {activity.time}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Analytics Charts Placeholder */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Analytics Overview</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-700 mb-4">Project Status Distribution</h3>
                <div className="space-y-3">
                  {[
                    { name: 'Active', value: 18, color: 'bg-blue-600' },
                    { name: 'Completed', value: 4, color: 'bg-green-600' },
                    { name: 'Draft', value: 2, color: 'bg-gray-600' }
                  ].map((item) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">{item.name}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${item.color} rounded-full`}
                            style={{ width: `${(item.value / 24) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{item.value}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-700 mb-4">Building Types</h3>
                <div className="space-y-3">
                  {[
                    { name: 'Commercial', value: 10, color: 'bg-purple-600' },
                    { name: 'Residential', value: 8, color: 'bg-green-600' },
                    { name: 'Industrial', value: 4, color: 'bg-yellow-600' },
                    { name: 'Mixed Use', value: 2, color: 'bg-red-600' }
                  ].map((item) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">{item.name}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${item.color} rounded-full`}
                            style={{ width: `${(item.value / 24) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{item.value}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-700 mb-4">Monthly Trends</h3>
                <div className="space-y-3">
                  {[
                    { name: 'Projects Created', value: 12, trend: '+15%' },
                    { name: 'Analyses Run', value: 45, trend: '+25%' },
                    { name: 'Shares Created', value: 8, trend: '+10%' }
                  ].map((item) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">{item.name}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-orange-500 rounded-full"
                            style={{ width: `${Math.random() * 60 + 40}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 flex items-center">
                          <ArrowUpRight className="w-3 h-3 mr-1 text-green-600" />
                          {item.trend}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Create Share Link Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4 border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create Share Link</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Select Project</label>
                <select
                  value={selectedProject}
                  onChange={(e) => setSelectedProject(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-gray-900"
                >
                  <option value="">Choose a project...</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name} ({project.client_name || 'No client'})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Link Expiry</label>
                <select
                  value={shareExpiry}
                  onChange={(e) => setShareExpiry(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-gray-900"
                >
                  <option value="1">1 day</option>
                  <option value="7">7 days</option>
                  <option value="30">30 days</option>
                  <option value="90">90 days</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowShareModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateShareLink}
                disabled={!selectedProject}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
              >
                Create Link
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
