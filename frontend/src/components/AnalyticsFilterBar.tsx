import { useState } from 'react'
import { Filter, X, Calendar } from 'lucide-react'

interface FilterState {
  startDate: string
  endDate: string
  organizationId: string | null
  projectId: string | null
  region: string | null
  buildingType: string | null
}

interface AnalyticsFilterBarProps {
  filters: FilterState
  onFiltersChange: (filters: FilterState) => void
  organizations: { id: string; name: string }[]
  projects: { id: string; name: string }[]
}

export default function AnalyticsFilterBar({
  filters,
  onFiltersChange,
  organizations,
  projects
}: AnalyticsFilterBarProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const handleFilterChange = (key: keyof FilterState, value: string | null) => {
    onFiltersChange({
      ...filters,
      [key]: value
    })
  }

  const clearFilters = () => {
    onFiltersChange({
      startDate: '',
      endDate: '',
      organizationId: null,
      projectId: null,
      region: null,
      buildingType: null
    })
  }

  const hasActiveFilters = Object.values(filters).some(v => v !== null && v !== '')

  const buildingTypes = ['Residential', 'Commercial', 'Industrial', 'Mixed Use', 'Institutional']
  const regions = ['North', 'South', 'East', 'West', 'Central']

  return (
    <div className="bg-paper rounded-xl border border-ink/10 mb-6">
      <div className="px-6 py-4 border-b border-ink/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-ink/60" />
          <span className="font-medium text-ink">Filters</span>
          {hasActiveFilters && (
            <span className="px-2 py-0.5 bg-accent/10 text-accent text-xs rounded-full">
              Active
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-sm text-ink/70 hover:text-ink flex items-center"
            >
              <X className="w-4 h-4 mr-1" />
              Clear All
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-sm text-accent hover:text-accent/80"
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="p-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={filters.startDate}
                onChange={(e) => handleFilterChange('startDate', e.target.value)}
                className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                End Date
              </label>
              <input
                type="date"
                value={filters.endDate}
                onChange={(e) => handleFilterChange('endDate', e.target.value)}
                className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
              />
            </div>

            {/* Organization */}
            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                Organization
              </label>
              <select
                value={filters.organizationId || ''}
                onChange={(e) => handleFilterChange('organizationId', e.target.value || null)}
                className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
              >
                <option value="">All Organizations</option>
                {organizations.map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Project */}
            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                Project
              </label>
              <select
                value={filters.projectId || ''}
                onChange={(e) => handleFilterChange('projectId', e.target.value || null)}
                className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
              >
                <option value="">All Projects</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Region */}
            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                Region
              </label>
              <select
                value={filters.region || ''}
                onChange={(e) => handleFilterChange('region', e.target.value || null)}
                className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
              >
                <option value="">All Regions</option>
                {regions.map((region) => (
                  <option key={region} value={region}>
                    {region}
                  </option>
                ))}
              </select>
            </div>

            {/* Building Type */}
            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                Building Type
              </label>
              <select
                value={filters.buildingType || ''}
                onChange={(e) => handleFilterChange('buildingType', e.target.value || null)}
                className="w-full border border-ink/15 rounded-lg px-3 py-2 bg-paper text-ink"
              >
                <option value="">All Types</option>
                {buildingTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
