import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import { projectsApi, organizationsApi, blueprintFilesApi } from '@/lib/api'
import { Plus, FolderOpen, Calendar, MapPin, Building2, FileText, X, Eye, GitCompare, Share2, BarChart3 } from 'lucide-react'
import AdvancedSearch from '@/components/AdvancedSearch'

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

interface Organization {
  id: string
  name: string
  slug: string
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
  const [projects, setProjects] = useState<Project[]>([])
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [recentFiles, setRecentFiles] = useState<BlueprintFile[]>([])
  const [selectedOrg, setSelectedOrg] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showCreateOrgModal, setShowCreateOrgModal] = useState(false)
  const [selectedFileForBoq, setSelectedFileForBoq] = useState<BlueprintFile | null>(null)
  const [newProject, setNewProject] = useState({
    name: '',
    code: '',
    client_name: '',
    location_city: '',
    location_state: '',
    building_type: 'residential',
  })
  const [newOrganization, setNewOrganization] = useState({
    name: '',
    slug: '',
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
  }, [location.pathname]) // Refresh on navigation changes

  const loadData = async () => {
    try {
      setLoading(true)
      const [orgsData, projectsData, filesData] = await Promise.all([
        organizationsApi.list(),
        projectsApi.list(),
        blueprintFilesApi.list(undefined, 5),
      ])
      setOrganizations(orgsData)
      setProjects(projectsData)
      setRecentFiles(filesData)
      if (orgsData.length > 0) {
        setSelectedOrg(orgsData[0].id)
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProject = async () => {
    console.log('handleCreateProject called')
    console.log('selectedOrg:', selectedOrg)
    console.log('newProject.name:', newProject.name)
    console.log('organizations:', organizations)
    
    if (!selectedOrg) {
      alert('Please select an organization first')
      return
    }
    
    if (!newProject.name || newProject.name.trim() === '') {
      alert('Please enter a project name')
      return
    }
    
    try {
      console.log('Creating project with data:', {
        organization_id: selectedOrg,
        ...newProject,
      })
      
      const createdProject = await projectsApi.create({
        organization_id: selectedOrg,
        ...newProject,
      })
      
      console.log('Project created successfully:', createdProject)
      setProjects([...projects, createdProject])
      setShowCreateModal(false)
      setNewProject({
        name: '',
        code: '',
        client_name: '',
        location_city: '',
        location_state: '',
        building_type: 'residential',
      })
    } catch (error) {
      console.error('Failed to create project:', error)
      alert(`Failed to create project: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  const handleCreateOrganization = async () => {
    if (!newOrganization.name || newOrganization.name.trim() === '') {
      alert('Please enter an organization name')
      return
    }
    
    try {
      console.log('Creating organization with data:', newOrganization)
      console.log('API_BASE_URL:', import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1')
      
      const createdOrg = await organizationsApi.create({
        name: newOrganization.name,
        slug: newOrganization.slug || newOrganization.name.toLowerCase().replace(/\s+/g, '-'),
      })
      
      console.log('Organization created successfully:', createdOrg)
      setOrganizations([...organizations, createdOrg])
      setSelectedOrg(createdOrg.id)
      setShowCreateOrgModal(false)
      setNewOrganization({
        name: '',
        slug: '',
      })
    } catch (error) {
      console.error('Failed to create organization:', error)
      console.error('Error details:', error)
      alert(`Failed to create organization: ${error instanceof Error ? error.message : 'Unknown error'}`)
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
    <div className="min-h-screen bg-paper">
      {/* Header */}
      <header className="bg-paper border-b border-ink/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-ink">Dashboard</h1>
              {organizations.length > 0 ? (
                <>
                  <select
                    value={selectedOrg || ''}
                    onChange={(e) => setSelectedOrg(e.target.value)}
                    className="border border-ink/15 rounded-lg px-3 py-1.5 text-sm bg-paper text-ink"
                  >
                    {organizations.map((org) => (
                      <option key={org.id} value={org.id}>
                        {org.name}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={() => setShowCreateOrgModal(true)}
                    className="text-sm text-accent hover:text-accent/80"
                  >
                    + New Organization
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setShowCreateOrgModal(true)}
                  className="text-sm text-accent hover:text-accent/80"
                >
                  + Create Organization
                </button>
              )}
            </div>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 bg-accent text-paper px-4 py-2 rounded-lg hover:bg-accent/90"
            >
              <Plus className="w-4 h-4" />
              New Project
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Bar */}
        <div className="mb-6">
          <AdvancedSearch 
            onSearch={(results) => console.log('Search results:', results)}
            placeholder="Search projects, blueprints, and more..."
          />
        </div>
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-paper rounded-xl p-6 border border-ink/10">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-ink/60">Total Projects</p>
                <p className="text-3xl font-bold text-ink">{projects.length}</p>
              </div>
              <FolderOpen className="w-8 h-8 text-accent" />
            </div>
          </div>
          <div className="bg-paper rounded-xl p-6 border border-ink/10">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-ink/60">Active</p>
                <p className="text-3xl font-bold text-ink">
                  {projects.filter(p => p.status === 'active').length}
                </p>
              </div>
              <Building2 className="w-8 h-8 text-green-500" />
            </div>
          </div>
          <div className="bg-paper rounded-xl p-6 border border-ink/10">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-ink/60">Blueprints Analyzed</p>
                <p className="text-3xl font-bold text-ink">{recentFiles.length}</p>
              </div>
              <FileText className="w-8 h-8 text-yellow-500" />
            </div>
          </div>
          <div className="bg-paper rounded-xl p-6 border border-ink/10">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-ink/60">Total Area (sq ft)</p>
                <p className="text-3xl font-bold text-ink">
                  {recentFiles.reduce((sum, f) => sum + (f.total_area || 0), 0).toLocaleString()}
                </p>
              </div>
              <MapPin className="w-8 h-8 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-paper rounded-xl border border-ink/10 mb-8 p-6">
          <h2 className="text-lg font-semibold text-ink mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex flex-col items-center p-4 rounded-lg border border-ink/10 hover:bg-paper-2 transition"
            >
              <Plus className="w-8 h-8 text-accent mb-2" />
              <span className="text-sm font-medium text-ink">New Project</span>
            </button>
            <button
              onClick={() => navigate('/upload')}
              className="flex flex-col items-center p-4 rounded-lg border border-ink/10 hover:bg-paper-2 transition"
            >
              <FileText className="w-8 h-8 text-green-500 mb-2" />
              <span className="text-sm font-medium text-ink">Upload Blueprint</span>
            </button>
            <button
              onClick={() => navigate('/exports')}
              className="flex flex-col items-center p-4 rounded-lg border border-ink/10 hover:bg-paper-2 transition"
            >
              <FolderOpen className="w-8 h-8 text-purple-500 mb-2" />
              <span className="text-sm font-medium text-ink">View Exports</span>
            </button>
            <button
              onClick={() => navigate('/enterprise-dashboard')}
              className="flex flex-col items-center p-4 rounded-lg border border-ink/10 hover:bg-paper-2 transition"
            >
              <BarChart3 className="w-8 h-8 text-yellow-500 mb-2" />
              <span className="text-sm font-medium text-ink">Analytics</span>
            </button>
          </div>
        </div>

        {/* Recent Files */}
        {recentFiles.length > 0 && (
          <div className="bg-paper rounded-xl border border-ink/10 mb-8">
            <div className="px-6 py-4 border-b border-ink/10">
              <h2 className="text-lg font-semibold text-ink">Recent Files</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-paper-2">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      File
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Area
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Rooms
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Analyzed
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink/10">
                  {recentFiles.map((file) => (
                    <tr key={file.id} className="hover:bg-paper-2">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <FileText className="w-5 h-5 text-ink/40 mr-3" />
                          <div className="font-medium text-ink">{file.filename}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          file.status === 'analyzed' ? 'bg-green-500/10 text-green-500' : 'bg-ink/10 text-ink/60'
                        }`}>
                          {file.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-ink/70">
                        {file.total_area ? `${file.total_area} sq ft` : '-'}
                      </td>
                      <td className="px-6 py-4 text-ink/70">
                        {file.room_count || '-'}
                      </td>
                      <td className="px-6 py-4 text-ink/70 text-sm">
                        {file.analyzed_at ? new Date(file.analyzed_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="px-6 py-4">
                        {file.status === 'analyzed' && (
                          <button
                            onClick={async () => {
                              try {
                                const fullFile = await blueprintFilesApi.get(file.id)
                                setSelectedFileForBoq(fullFile)
                              } catch (error) {
                                console.error('Failed to fetch file details:', error)
                                // Fallback to using the file from the list
                                setSelectedFileForBoq(file)
                              }
                            }}
                            className="text-accent hover:text-accent/80 text-sm font-medium"
                          >
                            <Eye className="w-4 h-4 inline mr-1" />
                            View BOQ
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Recent BOQ Section */}
        {recentFiles.length > 0 && (
          <div className="bg-paper rounded-xl border border-ink/10 mb-8">
            <div className="px-6 py-4 border-b border-ink/10 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-ink">Recent Files</h2>
              <div className="flex gap-3">
                {recentFiles.filter(f => f.status === 'analyzed').length >= 2 && (
                  <button
                    onClick={() => navigate('/floor-comparison/default')}
                    className="text-accent hover:text-accent/80 text-sm font-medium flex items-center"
                  >
                    <GitCompare className="w-4 h-4 mr-1" />
                    Compare Floors
                  </button>
                )}
                {recentFiles.filter(f => f.status === 'analyzed').length >= 1 && (
                  <button
                    onClick={() => navigate('/public-share/default')}
                    className="text-accent hover:text-accent/80 text-sm font-medium flex items-center"
                  >
                    <Share2 className="w-4 h-4 mr-1" />
                    Client Share Portal
                  </button>
                )}
                {projects.length >= 1 && (
                  <button
                    onClick={() => navigate(`/cost-benchmarking/${projects[0].id}`)}
                    className="text-accent hover:text-accent/80 text-sm font-medium flex items-center"
                  >
                    <BarChart3 className="w-4 h-4 mr-1" />
                    Cost Benchmarking
                  </button>
                )}
              </div>
            </div>
            <div className="p-6">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {recentFiles.slice(0, 6).map((file) => {
                  const boqTotal = file.analysis_result?.boq?.reduce(
                    (sum: number, item: any) => sum + (item.amount || 0),
                    0
                  ) || 0
                  return (
                    <div
                      key={file.id}
                      className="border border-ink/10 rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                      onClick={async () => {
                        try {
                          const fullFile = await blueprintFilesApi.get(file.id)
                          setSelectedFileForBoq(fullFile)
                        } catch (error) {
                          console.error('Failed to fetch file details:', error)
                          setSelectedFileForBoq(file)
                        }
                      }}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          <FileText className="w-5 h-5 text-ink/40 mr-2" />
                          <div className="font-medium text-ink truncate text-sm">
                            {file.filename}
                          </div>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          file.status === 'analyzed' ? 'bg-green-500/10 text-green-500' :
                          file.status === 'processing' ? 'bg-yellow-500/10 text-yellow-500' :
                          'bg-ink/10 text-ink/60'
                        }`}>
                          {file.status}
                        </span>
                      </div>
                      <div className="space-y-2">
                        {file.status === 'analyzed' && file.analysis_result?.boq ? (
                          <>
                            <div className="flex justify-between text-sm">
                              <span className="text-ink/70">Items:</span>
                              <span className="font-medium text-ink">{file.analysis_result.boq.length}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-ink/70">Total:</span>
                              <span className="font-semibold text-green-500">{formatInr(boqTotal)}</span>
                            </div>
                          </>
                        ) : (
                          <div className="text-sm text-ink/50">
                            {file.status === 'uploaded' ? 'Ready to analyze' : 'Processing...'}
                          </div>
                        )}
                        <div className="flex justify-between text-sm">
                          <span className="text-ink/70">Area:</span>
                          <span className="font-medium text-ink">{file.total_area ? `${file.total_area} sq ft` : '-'}</span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        {/* Projects Table */}
        <div className="bg-paper rounded-xl border border-ink/10">
          <div className="px-6 py-4 border-b border-ink/10">
            <h2 className="text-lg font-semibold text-ink">Projects</h2>
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
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Project
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Client
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink/10">
                  {projects.map((project) => (
                    <tr key={project.id} className="hover:bg-paper-2">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <FolderOpen className="w-5 h-5 text-ink/40 mr-3" />
                          <div>
                            <div className="font-medium text-ink">{project.name}</div>
                            {project.code && (
                              <div className="text-sm text-ink/50">{project.code}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-ink/70">
                        {project.client_name || '-'}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center text-ink/70">
                          <MapPin className="w-4 h-4 mr-1" />
                          {project.location_city && project.location_state
                            ? `${project.location_city}, ${project.location_state}`
                            : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-ink/70">
                        {project.building_type || '-'}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          project.status === 'active' ? 'bg-green-500/10 text-green-500' :
                          project.status === 'completed' ? 'bg-accent/10 text-accent' :
                          project.status === 'draft' ? 'bg-ink/10 text-ink/60' :
                          'bg-yellow-500/10 text-yellow-500'
                        }`}>
                          {project.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-ink/70 text-sm">
                        {new Date(project.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => navigate(`/project/${project.id}`)}
                          className="text-accent hover:text-accent/80 text-sm font-medium"
                        >
                          Open
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Create Organization Modal */}
      {showCreateOrgModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-paper rounded-xl p-6 w-full max-w-md mx-4 border border-ink/10">
            <h2 className="text-xl font-bold text-ink mb-4">Create Organization</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Organization Name *</label>
                <input
                  type="text"
                  value={newOrganization.name}
                  onChange={(e) => setNewOrganization({ ...newOrganization, name: e.target.value })}
                  className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
                  placeholder="Enter organization name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Slug (optional)</label>
                <input
                  type="text"
                  value={newOrganization.slug}
                  onChange={(e) => setNewOrganization({ ...newOrganization, slug: e.target.value })}
                  className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
                  placeholder="Auto-generated from name"
                />
                <p className="text-xs text-ink/50 mt-1">Leave blank to auto-generate from name</p>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateOrgModal(false)}
                className="px-4 py-2 border border-ink/15 rounded-lg hover:bg-paper-2"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateOrganization}
                disabled={!newOrganization.name}
                className="px-4 py-2 bg-accent text-paper rounded-lg hover:bg-accent/90 disabled:bg-ink/20"
              >
                Create Organization
              </button>
            </div>
          </div>
        </div>
      )}

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
