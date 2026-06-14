import { useState, useEffect } from 'react'
import { Search, X, Filter, Calendar, MapPin, Building2, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'
import { projectsApi, blueprintFilesApi } from '@/lib/api'

interface SearchFilters {
  query: string
  dateRange: string
  location: string
  buildingType: string
  status: string
  fileType: string
}

interface SearchResult {
  id: string
  type: 'project' | 'blueprint'
  title: string
  subtitle: string
  url: string
}

interface AdvancedSearchProps {
  onSearch: (results: SearchResult[]) => void
  placeholder?: string
}

export default function AdvancedSearch({ onSearch, placeholder = "Search projects, blueprints, and more..." }: AdvancedSearchProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    dateRange: '',
    location: '',
    buildingType: '',
    status: '',
    fileType: ''
  })
  const [projects, setProjects] = useState<any[]>([])
  const [blueprintFiles, setBlueprintFiles] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

  const loadData = async () => {
    try {
      setLoading(true)
      const [projectsData, filesData] = await Promise.all([
        projectsApi.list(),
        blueprintFilesApi.list()
      ])
      setProjects(projectsData)
      setBlueprintFiles(filesData)
    } catch (error) {
      console.error('Failed to load search data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    const results: SearchResult[] = []

    // Search projects
    projects.forEach(project => {
      const matchesQuery = !filters.query || 
        project.name.toLowerCase().includes(filters.query.toLowerCase()) ||
        (project.client_name && project.client_name.toLowerCase().includes(filters.query.toLowerCase()))
      const matchesLocation = !filters.location || 
        (project.location_city && project.location_city.toLowerCase().includes(filters.location.toLowerCase())) ||
        (project.location_state && project.location_state.toLowerCase().includes(filters.location.toLowerCase()))
      const matchesBuildingType = !filters.buildingType || 
        project.building_type === filters.buildingType
      const matchesStatus = !filters.status || 
        project.status === filters.status

      if (matchesQuery && matchesLocation && matchesBuildingType && matchesStatus) {
        results.push({
          id: project.id,
          type: 'project',
          title: project.name,
          subtitle: project.client_name || 'No client',
          url: `/project/${project.id}`
        })
      }
    })

    // Search blueprint files
    blueprintFiles.forEach(file => {
      const matchesQuery = !filters.query || 
        file.filename.toLowerCase().includes(filters.query.toLowerCase())
      const matchesStatus = !filters.status || 
        file.status === filters.status

      if (matchesQuery && matchesStatus) {
        const project = projects.find(p => p.id === file.project_id)
        results.push({
          id: file.id,
          type: 'blueprint',
          title: file.filename,
          subtitle: project?.name || 'Unknown Project',
          url: `/blueprint/${file.id}`
        })
      }
    })

    onSearch(results)
    setIsOpen(false)
  }

  const clearFilters = () => {
    setFilters({
      query: '',
      dateRange: '',
      location: '',
      buildingType: '',
      status: '',
      fileType: ''
    })
  }

  return (
    <div className="relative">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink/50" />
        <input
          type="text"
          placeholder={placeholder}
          value={filters.query}
          onChange={(e) => setFilters({ ...filters, query: e.target.value })}
          onFocus={() => setIsOpen(true)}
          className="w-full rounded-lg border border-ink/15 bg-paper pl-10 pr-10 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
        {filters.query && (
          <button
            onClick={() => setFilters({ ...filters, query: '' })}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/50 hover:text-ink"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Advanced Filters Panel */}
      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full left-0 right-0 z-50 mt-2 rounded-lg border border-ink/10 bg-paper shadow-xl">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-ink/70" />
                  <h3 className="text-sm font-medium text-ink">Advanced Filters</h3>
                </div>
                <button
                  onClick={clearFilters}
                  className="text-xs text-accent hover:text-accent/80"
                >
                  Clear All
                </button>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {/* Date Range */}
                <div>
                  <label className="block text-xs font-medium text-ink mb-1">Date Range</label>
                  <select
                    value={filters.dateRange}
                    onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
                    className="w-full rounded-md border border-ink/15 bg-paper px-3 py-2 text-xs text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="">All Time</option>
                    <option value="today">Today</option>
                    <option value="week">This Week</option>
                    <option value="month">This Month</option>
                    <option value="quarter">This Quarter</option>
                    <option value="year">This Year</option>
                  </select>
                </div>

                {/* Location */}
                <div>
                  <label className="block text-xs font-medium text-ink mb-1">Location</label>
                  <div className="relative">
                    <MapPin className="absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-ink/50" />
                    <input
                      type="text"
                      placeholder="City or State"
                      value={filters.location}
                      onChange={(e) => setFilters({ ...filters, location: e.target.value })}
                      className="w-full rounded-md border border-ink/15 bg-paper pl-8 pr-3 py-2 text-xs text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                    />
                  </div>
                </div>

                {/* Building Type */}
                <div>
                  <label className="block text-xs font-medium text-ink mb-1">Building Type</label>
                  <div className="relative">
                    <Building2 className="absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-ink/50" />
                    <select
                      value={filters.buildingType}
                      onChange={(e) => setFilters({ ...filters, buildingType: e.target.value })}
                      className="w-full rounded-md border border-ink/15 bg-paper pl-8 pr-3 py-2 text-xs text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="">All Types</option>
                      <option value="residential">Residential</option>
                      <option value="commercial">Commercial</option>
                      <option value="industrial">Industrial</option>
                      <option value="mixed">Mixed Use</option>
                    </select>
                  </div>
                </div>

                {/* Status */}
                <div>
                  <label className="block text-xs font-medium text-ink mb-1">Status</label>
                  <select
                    value={filters.status}
                    onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                    className="w-full rounded-md border border-ink/15 bg-paper px-3 py-2 text-xs text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>

                {/* File Type */}
                <div>
                  <label className="block text-xs font-medium text-ink mb-1">File Type</label>
                  <div className="relative">
                    <FileText className="absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-ink/50" />
                    <select
                      value={filters.fileType}
                      onChange={(e) => setFilters({ ...filters, fileType: e.target.value })}
                      className="w-full rounded-md border border-ink/15 bg-paper pl-8 pr-3 py-2 text-xs text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="">All Files</option>
                      <option value="pdf">PDF</option>
                      <option value="png">PNG</option>
                      <option value="jpg">JPG</option>
                      <option value="dxf">DXF</option>
                      <option value="dwg">DWG</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-4 flex gap-2">
                <button
                  onClick={handleSearch}
                  className="flex-1 rounded-lg bg-ink px-4 py-2 text-sm font-medium text-paper transition hover:bg-ink/90"
                >
                  Search
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="rounded-lg border border-ink/15 bg-paper px-4 py-2 text-sm text-ink transition hover:bg-paper-2"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
