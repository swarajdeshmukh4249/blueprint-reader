import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Plus, 
  FolderOpen, 
  Building2, 
  FileText, 
  GitCompare, 
  BarChart3,
  TrendingUp,
  Users,
  MapPin,
  Calendar,
  MoreVertical,
  Search,
  Filter,
  Grid,
  List,
  Clock,
  Trash2
} from 'lucide-react'

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
  floor_count: number
  analysis_count: number
  total_area: number
}

type ViewMode = 'grid' | 'list'

export default function NewDashboard() {
  const navigate = useNavigate()
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [searchQuery, setSearchQuery] = useState('')

  // Dummy data
  const [projects] = useState<Project[]>([
    {
      id: '1',
      name: 'Skyline Tower',
      code: 'PRJ-001',
      client_name: 'ABC Developers',
      location_city: 'Mumbai',
      location_state: 'Maharashtra',
      building_type: 'commercial',
      status: 'active',
      created_at: '2024-01-15',
      floor_count: 15,
      analysis_count: 12,
      total_area: 45000
    },
    {
      id: '2',
      name: 'Green Valley Residency',
      code: 'PRJ-002',
      client_name: 'XYZ Construction',
      location_city: 'Pune',
      location_state: 'Maharashtra',
      building_type: 'residential',
      status: 'completed',
      created_at: '2024-02-20',
      floor_count: 8,
      analysis_count: 8,
      total_area: 28000
    },
    {
      id: '3',
      name: 'Tech Park Phase 1',
      code: 'PRJ-003',
      client_name: 'TechCorp India',
      location_city: 'Bangalore',
      location_state: 'Karnataka',
      building_type: 'commercial',
      status: 'active',
      created_at: '2024-03-10',
      floor_count: 20,
      analysis_count: 18,
      total_area: 65000
    },
    {
      id: '4',
      name: 'Riverside Apartments',
      code: 'PRJ-004',
      client_name: 'Riverfront Builders',
      location_city: 'Delhi',
      location_state: 'Delhi',
      building_type: 'residential',
      status: 'draft',
      created_at: '2024-04-05',
      floor_count: 12,
      analysis_count: 5,
      total_area: 32000
    },
    {
      id: '5',
      name: 'Industrial Complex B',
      code: 'PRJ-005',
      client_name: 'Manufacturing Co',
      location_city: 'Chennai',
      location_state: 'Tamil Nadu',
      building_type: 'industrial',
      status: 'active',
      created_at: '2024-05-12',
      floor_count: 6,
      analysis_count: 6,
      total_area: 18000
    },
    {
      id: '6',
      name: 'Mixed Use Development',
      code: 'PRJ-006',
      client_name: 'City Developers',
      location_city: 'Hyderabad',
      location_state: 'Telangana',
      building_type: 'mixed_use',
      status: 'on_hold',
      created_at: '2024-06-01',
      floor_count: 25,
      analysis_count: 20,
      total_area: 75000
    }
  ])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500/10 text-green-500'
      case 'completed': return 'bg-blue-500/10 text-blue-500'
      case 'draft': return 'bg-gray-500/10 text-gray-500'
      case 'on_hold': return 'bg-yellow-500/10 text-yellow-500'
      default: return 'bg-gray-500/10 text-gray-500'
    }
  }

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.client_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.location_city?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-gray-900">Project Dashboard</h1>
              <span className="text-sm text-gray-500">{projects.length} projects</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center bg-gray-100 rounded-lg border border-gray-200">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 ${viewMode === 'grid' ? 'text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  <Grid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 ${viewMode === 'list' ? 'text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
              <button 
                className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                New Project
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Projects</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{projects.length}</p>
                <p className="text-xs text-green-600 mt-1 flex items-center">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  +12% this month
                </p>
              </div>
              <FolderOpen className="w-7 h-7 text-blue-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Active</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {projects.filter(p => p.status === 'active').length}
                </p>
                <p className="text-xs text-gray-500 mt-1">Currently in progress</p>
              </div>
              <Building2 className="w-7 h-7 text-green-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Floors</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {projects.reduce((sum, p) => sum + p.floor_count, 0)}
                </p>
                <p className="text-xs text-gray-500 mt-1">Across all projects</p>
              </div>
              <FileText className="w-7 h-7 text-yellow-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Area</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {projects.reduce((sum, p) => sum + p.total_area, 0).toLocaleString()}
                </p>
                <p className="text-xs text-gray-500 mt-1">sq ft analyzed</p>
              </div>
              <MapPin className="w-7 h-7 text-purple-600" />
            </div>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search projects, clients, locations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
              <Filter className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg border border-gray-200 mb-8 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <button className="flex flex-col items-center p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all">
              <Plus className="w-7 h-7 text-blue-600 mb-2" />
              <span className="text-xs font-medium text-gray-700">New Project</span>
            </button>
            <button className="flex flex-col items-center p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all">
              <FileText className="w-7 h-7 text-green-600 mb-2" />
              <span className="text-xs font-medium text-gray-700">Upload Blueprint</span>
            </button>
            <button className="flex flex-col items-center p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all">
              <GitCompare className="w-7 h-7 text-yellow-600 mb-2" />
              <span className="text-xs font-medium text-gray-700">Compare Floors</span>
            </button>
            <button 
              onClick={() => navigate('/new-analytics')}
              className="flex flex-col items-center p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all"
            >
              <BarChart3 className="w-7 h-7 text-purple-600 mb-2" />
              <span className="text-xs font-medium text-gray-700">View Analytics</span>
            </button>
          </div>
        </div>

        {/* Projects Grid/List */}
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {filteredProjects.map((project) => (
              <div 
                key={project.id}
                className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-all cursor-pointer"
              >
                <div className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">{project.name}</h3>
                      {project.code && (
                        <p className="text-xs text-gray-500">{project.code}</p>
                      )}
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                      {project.status}
                    </span>
                  </div>
                  
                  <div className="space-y-2 mb-4">
                    {project.client_name && (
                      <div className="flex items-center text-sm text-gray-600">
                        <Users className="w-4 h-4 mr-2" />
                        {project.client_name}
                      </div>
                    )}
                    {project.location_city && (
                      <div className="flex items-center text-sm text-gray-600">
                        <MapPin className="w-4 h-4 mr-2" />
                        {project.location_city}, {project.location_state}
                      </div>
                    )}
                    <div className="flex items-center text-sm text-gray-600">
                      <Building2 className="w-4 h-4 mr-2" />
                      {project.building_type || 'Not specified'}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-3 border-t border-gray-100">
                    <div className="text-center">
                      <p className="text-xs text-gray-500">Floors</p>
                      <p className="text-sm font-semibold text-gray-900">{project.floor_count}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500">Analyzed</p>
                      <p className="text-sm font-semibold text-gray-900">{project.analysis_count}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500">Area</p>
                      <p className="text-sm font-semibold text-gray-900">{(project.total_area / 1000).toFixed(0)}k</p>
                    </div>
                  </div>
                </div>

                <div className="px-5 py-3 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    {new Date(project.created_at).toLocaleDateString()}
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                      Open
                    </button>
                    <button className="text-red-500 hover:text-red-600">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm mb-8">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Project
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Client
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Floors
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Area
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredProjects.map((project) => (
                    <tr key={project.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <FolderOpen className="w-5 h-5 text-gray-400 mr-3" />
                          <div>
                            <div className="font-medium text-gray-900">{project.name}</div>
                            {project.code && (
                              <div className="text-sm text-gray-500">{project.code}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-600">
                        {project.client_name || '-'}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center text-gray-600">
                          <MapPin className="w-4 h-4 mr-1" />
                          {project.location_city && project.location_state
                            ? `${project.location_city}, ${project.location_state}`
                            : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-600">
                        {project.building_type || '-'}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                          {project.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-600">
                        {project.floor_count}
                      </td>
                      <td className="px-6 py-4 text-gray-600">
                        {project.total_area.toLocaleString()} sq ft
                      </td>
                      <td className="px-6 py-4 text-gray-600 text-sm">
                        {new Date(project.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                            Open
                          </button>
                          <button className="text-red-500 hover:text-red-600 text-sm font-medium">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
