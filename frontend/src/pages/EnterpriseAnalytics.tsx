import React, { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import AnalyticsFilterBar from '@/components/AnalyticsFilterBar'
import { organizationsApi, projectsApi } from '@/lib/api'
import { Download } from 'lucide-react'

// Types
interface KPICard {
  title: string
  value: string | number
  trend: number
  unit?: string
}

interface CostTrendData {
  date: string
  total_cost: number
  material_cost: number
  labour_cost: number
  overhead_cost: number
}

interface CostBreakdownData {
  category: string
  cost: number
  percentage: number
}

interface MaterialData {
  material_name: string
  quantity: number
  unit: string
  cost: number
}

interface RegionalRate {
  country: string
  state: string | null
  city: string
  material_name: string
  current_rate: number
  unit: string
  trend: string
  trend_percentage: number
}

interface AIQualityMetrics {
  total_rooms_detected: number
  high_confidence_rooms: number
  medium_confidence_rooms: number
  low_confidence_rooms: number
  rooms_corrected: number
  manual_corrections: number
  accuracy_rate: number
  avg_confidence_score: number
}

interface RoomTypeCorrection {
  room_type: string
  total_detections: number
  total_corrections: number
  correction_rate: number
}

interface RevisionData {
  from_version_id: string
  to_version_id: string
  area_change_sqft: number
  boq_change: number
  cost_change: number
  rooms_added: number
  rooms_deleted: number
  rooms_modified: number
  created_at: string
}

interface PortfolioMetrics {
  total_portfolio_value: number
  total_area_sqft: number
  total_buildings: number
  total_floors: number
  residential_count: number
  commercial_count: number
  industrial_count: number
  mixed_use_count: number
}

interface TeamActivityItem {
  user_id: string
  activity_date: string
  analyses_run: number
  reports_exported: number
  comments_added: number
  corrections_made: number
  approvals_given: number
}

interface ApprovalMetrics {
  pending_approvals: number
  approved_reports: number
  rejected_reports: number
  avg_approval_time_hours: number
}

// Colors
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

const EnterpriseAnalytics: React.FC = () => {
  const [activeTab, setActiveTab] = useState('executive')
  const [organizationId, setOrganizationId] = useState('demo-org-1')
  const [loading, setLoading] = useState(true)
  const [kpis, setKPIs] = useState<KPICard[]>([])
  const [costTrends, setCostTrends] = useState<CostTrendData[]>([])
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdownData[]>([])
  const [materialQuantities, setMaterialQuantities] = useState<MaterialData[]>([])
  const [regionalRates, setRegionalRates] = useState<RegionalRate[]>([])
  const [aiQuality, setAIQuality] = useState<AIQualityMetrics | null>(null)
  const [roomTypeCorrections, setRoomTypeCorrections] = useState<RoomTypeCorrection[]>([])
  const [revisions, setRevisions] = useState<RevisionData[]>([])
  const [portfolioMetrics, setPortfolioMetrics] = useState<PortfolioMetrics | null>(null)
  const [teamActivity, setTeamActivity] = useState<TeamActivityItem[]>([])
  const [approvalMetrics, setApprovalMetrics] = useState<ApprovalMetrics | null>(null)

  // Filter state
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    organizationId: null as string | null,
    projectId: null as string | null,
    region: null as string | null,
    buildingType: null as string | null
  })

  // Organizations and projects for filter dropdowns
  const [organizations, setOrganizations] = useState<{ id: string; name: string }[]>([])
  const [projects, setProjects] = useState<{ id: string; name: string }[]>([])

  // Load organizations and projects for filters
  useEffect(() => {
    const loadFilterData = async () => {
      try {
        const orgs = await organizationsApi.list()
        setOrganizations(orgs.map((o: any) => ({ id: o.id, name: o.name })))
        
        const projs = await projectsApi.list()
        setProjects(projs.map((p: any) => ({ id: p.id, name: p.name })))
      } catch (err) {
        console.error('Failed to load filter data:', err)
      }
    }
    loadFilterData()
  }, [])

  // Handle export
  const handleExport = async (format: 'pdf' | 'excel' | 'csv') => {
    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      
      // Build export data
      const exportData = {
        organization_id: filters.organizationId || organizationId,
        tab: activeTab,
        filters: filters,
        data: {
          kpis,
          costTrends,
          costBreakdown,
          materialQuantities,
          regionalRates,
          aiQuality,
          roomTypeCorrections,
          revisions,
          portfolioMetrics,
          teamActivity,
          approvalMetrics
        }
      }
      
      const response = await fetch(`${API_BASE}/analytics/export/${format}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportData),
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `analytics-${activeTab}-${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : format}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        console.error('Export failed')
      }
    } catch (err) {
      console.error('Export error:', err)
    }
  }

  // Fetch real data from backend APIs
  useEffect(() => {
    const fetchAnalyticsData = async () => {
      try {
        const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
        
        // Build query params from filters
        const queryParams = new URLSearchParams()
        if (filters.startDate) queryParams.append('start_date', filters.startDate)
        if (filters.endDate) queryParams.append('end_date', filters.endDate)
        if (filters.organizationId) queryParams.append('organization_id', filters.organizationId)
        if (filters.projectId) queryParams.append('project_id', filters.projectId)
        if (filters.region) queryParams.append('region', filters.region)
        if (filters.buildingType) queryParams.append('building_type', filters.buildingType)
        
        // Use filtered organization ID or default
        const orgId = filters.organizationId || organizationId
        const queryString = queryParams.toString()
        
        // Fetch Executive KPIs
        const kpisResponse = await fetch(`${API_BASE}/analytics/executive-kpis/${orgId}?period=monthly${queryString ? '&' + queryString : ''}`)
        if (kpisResponse.ok) {
          const kpisData = await kpisResponse.json()
          setKPIs([
            { title: 'Total Projects', value: kpisData.total_projects, trend: kpisData.projects_trend },
            { title: 'Active Projects', value: kpisData.active_projects, trend: 0 },
            { title: 'Completed Projects', value: kpisData.completed_projects, trend: 0 },
            { title: 'Total Floor Area', value: (kpisData.total_floor_area_sqft / 1000000).toFixed(1) + 'M', trend: kpisData.cost_per_sqft_trend, unit: 'sq ft' },
            { title: 'Total BOQ Value', value: '₹' + (kpisData.total_boq_value / 10000000).toFixed(1) + ' Cr', trend: kpisData.boq_value_trend },
            { title: 'Avg Cost/Sq Ft', value: '₹' + kpisData.avg_cost_per_sqft.toFixed(0), trend: kpisData.cost_per_sqft_trend },
            { title: 'Avg Project Cost', value: '₹' + (kpisData.avg_project_cost / 10000000).toFixed(1) + ' Cr', trend: 0 },
          ])
        }

        // Fetch Cost Trends
        const costTrendsResponse = await fetch(`${API_BASE}/analytics/cost-trends/${orgId}?${queryString || 'start_date=2024-01-01&end_date=2024-06-30'}`)
        if (costTrendsResponse.ok) {
          const costTrendsData = await costTrendsResponse.json()
          setCostTrends(costTrendsData.map((item: any) => ({
            date: new Date(item.date).toLocaleDateString('en-US', { month: 'short' }),
            total_cost: item.total_cost,
            material_cost: item.material_cost,
            labour_cost: item.labour_cost,
            overhead_cost: item.overhead_cost,
          })))
        }

        // Fetch Cost Breakdown
        const costBreakdownResponse = await fetch(`${API_BASE}/analytics/cost-breakdown/${organizationId}`)
        if (costBreakdownResponse.ok) {
          const costBreakdownData = await costBreakdownResponse.json()
          setCostBreakdown(costBreakdownData)
        }

        // Fetch Material Quantities
        const materialQuantitiesResponse = await fetch(`${API_BASE}/analytics/material-quantities/${organizationId}`)
        if (materialQuantitiesResponse.ok) {
          const materialQuantitiesData = await materialQuantitiesResponse.json()
          setMaterialQuantities(materialQuantitiesData)
        }

        // Fetch Regional Rates
        const regionalRatesResponse = await fetch(`${API_BASE}/analytics/regional-rates/${organizationId}`)
        if (regionalRatesResponse.ok) {
          const regionalRatesData = await regionalRatesResponse.json()
          setRegionalRates(regionalRatesData)
        }

        // Fetch AI Quality Metrics
        const aiQualityResponse = await fetch(`${API_BASE}/analytics/ai-quality/${organizationId}`)
        if (aiQualityResponse.ok) {
          const aiQualityData = await aiQualityResponse.json()
          setAIQuality(aiQualityData)
        }

        // Fetch Room Type Corrections
        const roomTypeCorrectionsResponse = await fetch(`${API_BASE}/analytics/room-type-corrections/${organizationId}`)
        if (roomTypeCorrectionsResponse.ok) {
          const roomTypeCorrectionsData = await roomTypeCorrectionsResponse.json()
          setRoomTypeCorrections(roomTypeCorrectionsData)
        }

        // Fetch Portfolio Metrics
        const portfolioResponse = await fetch(`${API_BASE}/analytics/portfolio/${organizationId}`)
        if (portfolioResponse.ok) {
          const portfolioData = await portfolioResponse.json()
          setPortfolioMetrics(portfolioData)
        }

        // Fetch Approval Metrics
        const approvalResponse = await fetch(`${API_BASE}/analytics/approval-metrics/${organizationId}`)
        if (approvalResponse.ok) {
          const approvalData = await approvalResponse.json()
          setApprovalMetrics(approvalData)
        }

      } catch (error) {
        console.error('Error fetching analytics data:', error)
        // Fall back to mock data if API fails
        setKPIs([
          { title: 'Total Projects', value: 0, trend: 0 },
          { title: 'Active Projects', value: 0, trend: 0 },
          { title: 'Completed Projects', value: 0, trend: 0 },
          { title: 'Total Floor Area', value: '0', trend: 0, unit: 'sq ft' },
          { title: 'Total BOQ Value', value: '₹0', trend: 0 },
          { title: 'Avg Cost/Sq Ft', value: '₹0', trend: 0 },
          { title: 'Avg Project Cost', value: '₹0', trend: 0 },
        ])
      } finally {
        setLoading(false)
      }
    }

    fetchAnalyticsData()
  }, [organizationId])

  const KPICard: React.FC<KPICard> = ({ title, value, trend, unit }) => (
    <div className="bg-paper rounded-lg shadow-md p-6 border border-ink/10">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-medium text-ink/60">{title}</p>
          <p className="text-2xl font-bold text-ink mt-1">
            {value} {unit && <span className="text-sm font-normal text-ink/60">{unit}</span>}
          </p>
        </div>
        <div className={`flex items-center text-sm ${trend >= 0 ? 'text-green-500' : 'text-red-500'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
        </div>
      </div>
      <p className="text-xs text-ink/40 mt-2">vs last month</p>
    </div>
  )

  const ExecutiveDashboard = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-ink">Executive KPI Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, index) => <KPICard key={index} {...kpi} />)}
      </div>
    </div>
  )

  const CostAnalytics = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-ink">Cost Analytics</h2>
      
      <div className="bg-paper rounded-lg shadow-md p-6 border border-ink/10">
        <h3 className="text-lg font-semibold mb-4 text-ink">Total Cost Trend</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={costTrends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="total_cost" stroke="#3b82f6" name="Total Cost" />
            <Line type="monotone" dataKey="material_cost" stroke="#10b981" name="Material Cost" />
            <Line type="monotone" dataKey="labour_cost" stroke="#f59e0b" name="Labour Cost" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-paper rounded-lg shadow-md p-6 border border-ink/10">
          <h3 className="text-lg font-semibold mb-4 text-ink">Cost Breakdown</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={costBreakdown}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ category, percentage }) => `${category} (${percentage}%)`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="cost"
              >
                {costBreakdown.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-paper rounded-lg shadow-md p-6 border border-ink/10">
          <h3 className="text-lg font-semibold mb-4 text-ink">Cost by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={costBreakdown}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="cost" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )

  const MaterialAnalytics = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-ink">Material Analytics</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {materialQuantities.map((material, index) => (
          <div key={index} className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
            <p className="text-sm font-medium text-ink/60">{material.material_name}</p>
            <p className="text-xl font-bold text-ink mt-1">{material.quantity.toLocaleString()}</p>
            <p className="text-xs text-ink/40">{material.unit}</p>
            <p className="text-sm font-semibold text-accent mt-2">₹{(material.cost / 100000).toFixed(1)}L</p>
          </div>
        ))}
      </div>

      <div className="bg-paper rounded-lg shadow-md p-6 border border-ink/10">
        <h3 className="text-lg font-semibold mb-4 text-ink">Material Cost Breakdown</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={materialQuantities}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="material_name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="cost" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )

  const RegionalCostIntelligence = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-ink">Regional Cost Intelligence</h2>
      
      <div className="bg-paper rounded-lg shadow-md overflow-hidden border border-ink/10">
        <table className="min-w-full divide-y divide-ink/10">
          <thead className="bg-paper-2">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">City</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Material</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Current Rate</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Trend</th>
            </tr>
          </thead>
          <tbody className="bg-paper divide-y divide-ink/10">
            {regionalRates.map((rate, index) => (
              <tr key={index}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{rate.city}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{rate.material_name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">₹{rate.current_rate.toLocaleString()}/{rate.unit}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    rate.trend === 'increasing' ? 'bg-red-500/10 text-red-500' :
                    rate.trend === 'decreasing' ? 'bg-green-500/10 text-green-500' :
                    'bg-ink/10 text-ink/60'
                  }`}>
                    {rate.trend} ({rate.trend_percentage}%)
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )

  const AIQualityDashboard = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-ink">AI Analysis Quality Dashboard</h2>
      
      {aiQuality && (
        <>
          <div className="bg-paper rounded-lg shadow-md p-6 border border-ink/10">
            <h3 className="text-lg font-semibold mb-4 text-ink">Confidence Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'High Confidence', value: aiQuality.high_confidence_rooms },
                    { name: 'Medium Confidence', value: aiQuality.medium_confidence_rooms },
                    { name: 'Low Confidence', value: aiQuality.low_confidence_rooms },
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  <Cell fill="#10b981" />
                  <Cell fill="#f59e0b" />
                  <Cell fill="#ef4444" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
              <p className="text-sm font-medium text-ink/60">Total Rooms Detected</p>
              <p className="text-2xl font-bold text-ink mt-1">{aiQuality.total_rooms_detected}</p>
            </div>
            <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
              <p className="text-sm font-medium text-ink/60">Rooms Corrected</p>
              <p className="text-2xl font-bold text-ink mt-1">{aiQuality.rooms_corrected}</p>
            </div>
            <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
              <p className="text-sm font-medium text-ink/60">Manual Corrections</p>
              <p className="text-2xl font-bold text-ink mt-1">{aiQuality.manual_corrections}</p>
            </div>
            <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
              <p className="text-sm font-medium text-ink/60">Accuracy Rate</p>
              <p className="text-2xl font-bold text-green-500 mt-1">{aiQuality.accuracy_rate}%</p>
            </div>
          </div>

          <div className="bg-paper rounded-lg shadow-md p-6 border border-ink/10">
            <h3 className="text-lg font-semibold mb-4 text-ink">Most Corrected Room Types</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={roomTypeCorrections}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="room_type" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="correction_rate" fill="#ef4444" name="Correction Rate %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  )

  const RevisionAnalytics = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-ink">Revision Analytics</h2>
      
      <div className="bg-paper rounded-lg shadow-md overflow-hidden border border-ink/10">
        <table className="min-w-full divide-y divide-ink/10">
          <thead className="bg-paper-2">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">From</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">To</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Area Change</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Cost Change</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Rooms Added</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Rooms Deleted</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Date</th>
            </tr>
          </thead>
          <tbody className="bg-paper divide-y divide-ink/10">
            {revisions.map((rev, index) => (
              <tr key={index}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{rev.from_version_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{rev.to_version_id}</td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${rev.area_change_sqft >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {rev.area_change_sqft >= 0 ? '+' : ''}{rev.area_change_sqft} sq ft
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${rev.cost_change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  ₹{(rev.cost_change / 1000).toFixed(0)}K
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{rev.rooms_added}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{rev.rooms_deleted}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink/50">{rev.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )

  const PortfolioAnalytics = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-ink">Portfolio Analytics</h2>
      
      {portfolioMetrics && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
              <p className="text-sm font-medium text-ink/60">Total Portfolio Value</p>
              <p className="text-2xl font-bold text-ink mt-1">₹{(portfolioMetrics.total_portfolio_value / 10000000).toFixed(1)} Cr</p>
            </div>
            <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
              <p className="text-sm font-medium text-ink/60">Total Area</p>
              <p className="text-2xl font-bold text-ink mt-1">{(portfolioMetrics.total_area_sqft / 1000000).toFixed(1)}M sq ft</p>
            </div>
            <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
              <p className="text-sm font-medium text-ink/60">Total Buildings</p>
              <p className="text-2xl font-bold text-ink mt-1">{portfolioMetrics.total_buildings}</p>
            </div>
            <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
              <p className="text-sm font-medium text-ink/60">Total Floors</p>
              <p className="text-2xl font-bold text-ink mt-1">{portfolioMetrics.total_floors}</p>
            </div>
          </div>

          <div className="bg-paper rounded-lg shadow-md p-6 border border-ink/10">
            <h3 className="text-lg font-semibold mb-4 text-ink">Project Distribution by Type</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Residential', value: portfolioMetrics.residential_count },
                    { name: 'Commercial', value: portfolioMetrics.commercial_count },
                    { name: 'Industrial', value: portfolioMetrics.industrial_count },
                    { name: 'Mixed Use', value: portfolioMetrics.mixed_use_count },
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  <Cell fill="#3b82f6" />
                  <Cell fill="#10b981" />
                  <Cell fill="#f59e0b" />
                  <Cell fill="#8b5cf6" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  )

  const TeamAnalytics = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-ink">Team Analytics</h2>
      
      <div className="bg-paper rounded-lg shadow-md overflow-hidden border border-ink/10">
        <table className="min-w-full divide-y divide-ink/10">
          <thead className="bg-paper-2">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">User</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Analyses</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Exports</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Comments</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Corrections</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ink/60 uppercase tracking-wider">Approvals</th>
            </tr>
          </thead>
          <tbody className="bg-paper divide-y divide-ink/10">
            {teamActivity.map((activity, index) => (
              <tr key={index}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{activity.user_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{activity.analyses_run}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{activity.reports_exported}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{activity.comments_added}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{activity.corrections_made}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-ink">{activity.approvals_given}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )

  const ApprovalAnalytics = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-ink">Approval Workflow Analytics</h2>
      
      {approvalMetrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
            <p className="text-sm font-medium text-ink/60">Pending Approvals</p>
            <p className="text-2xl font-bold text-yellow-500 mt-1">{approvalMetrics.pending_approvals}</p>
          </div>
          <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
            <p className="text-sm font-medium text-ink/60">Approved Reports</p>
            <p className="text-2xl font-bold text-green-500 mt-1">{approvalMetrics.approved_reports}</p>
          </div>
          <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
            <p className="text-sm font-medium text-ink/60">Rejected Reports</p>
            <p className="text-2xl font-bold text-red-500 mt-1">{approvalMetrics.rejected_reports}</p>
          </div>
          <div className="bg-paper rounded-lg shadow-md p-4 border border-ink/10">
            <p className="text-sm font-medium text-ink/60">Avg Approval Time</p>
            <p className="text-2xl font-bold text-ink mt-1">{approvalMetrics.avg_approval_time_hours}h</p>
          </div>
        </div>
      )}
    </div>
  )

  const AuditComplianceAnalytics = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-ink">Audit & Compliance Analytics</h2>
      
      <div className="bg-paper rounded-lg shadow-md p-6 border border-ink/10">
        <h3 className="text-lg font-semibold mb-4 text-ink">Audit Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-accent/10 rounded-lg p-4">
            <p className="text-sm font-medium text-accent">Uploads</p>
            <p className="text-2xl font-bold text-ink mt-1">1,245</p>
          </div>
          <div className="bg-green-500/10 rounded-lg p-4">
            <p className="text-sm font-medium text-green-500">Analyses</p>
            <p className="text-2xl font-bold text-ink mt-1">892</p>
          </div>
          <div className="bg-yellow-500/10 rounded-lg p-4">
            <p className="text-sm font-medium text-yellow-500">Corrections</p>
            <p className="text-2xl font-bold text-ink mt-1">156</p>
          </div>
          <div className="bg-purple-500/10 rounded-lg p-4">
            <p className="text-sm font-medium text-purple-500">Exports</p>
            <p className="text-2xl font-bold text-ink mt-1">423</p>
          </div>
          <div className="bg-red-500/10 rounded-lg p-4">
            <p className="text-sm font-medium text-red-500">Approvals</p>
            <p className="text-2xl font-bold text-ink mt-1">165</p>
          </div>
        </div>
      </div>

      <div className="bg-paper rounded-lg shadow-md p-6 border border-ink/10">
        <h3 className="text-lg font-semibold mb-4 text-ink">Recent Audit Logs</h3>
        <div className="space-y-3">
          {[
            { action: 'UPLOAD', user: 'user1', project: 'Project A', time: '2 hours ago' },
            { action: 'ANALYSIS', user: 'user2', project: 'Project B', time: '3 hours ago' },
            { action: 'CORRECTION', user: 'user3', project: 'Project A', time: '5 hours ago' },
            { action: 'EXPORT', user: 'user1', project: 'Project C', time: '6 hours ago' },
            { action: 'APPROVAL', user: 'user2', project: 'Project B', time: '1 day ago' },
          ].map((log, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-paper-2 rounded-lg">
              <div className="flex items-center space-x-4">
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-accent/10 text-accent">{log.action}</span>
                <span className="text-sm text-ink">{log.user}</span>
                <span className="text-sm text-ink/50">{log.project}</span>
              </div>
              <span className="text-xs text-ink/40">{log.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const BenchmarkingDashboard = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Benchmarking Dashboard</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Cost per Sq Ft Benchmarking</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={[
              { name: 'Your Project', value: 2250 },
              { name: 'Regional Avg', value: 2100 },
              { name: 'Industry Avg', value: 2400 },
            ]}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Material Usage Benchmarking</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={[
              { name: 'Steel', your: 2800, benchmark: 3000 },
              { name: 'Cement', your: 5200, benchmark: 4800 },
              { name: 'Sand', your: 8500, benchmark: 9000 },
            ]}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="your" fill="#10b981" name="Your Usage" />
              <Bar dataKey="benchmark" fill="#94a3b8" name="Benchmark" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Variance Analysis</h3>
        <div className="space-y-3">
          {[
            { metric: 'Cost/Sq Ft', your: 2250, benchmark: 2100, variance: 7.1 },
            { metric: 'Steel Usage', your: 2800, benchmark: 3000, variance: -6.7 },
            { metric: 'Cement Usage', your: 5200, benchmark: 4800, variance: 8.3 },
            { metric: 'Construction Time', your: 18, benchmark: 24, variance: -25.0 },
          ].map((item, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-900">{item.metric}</span>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">Your: {item.your}</span>
                <span className="text-sm text-gray-600">Benchmark: {item.benchmark}</span>
                <span className={`text-sm font-semibold ${item.variance >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {item.variance >= 0 ? '+' : ''}{item.variance}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const tabs = [
    { id: 'executive', label: 'Executive KPIs', component: ExecutiveDashboard },
    { id: 'cost', label: 'Cost Analytics', component: CostAnalytics },
    { id: 'material', label: 'Material Analytics', component: MaterialAnalytics },
    { id: 'regional', label: 'Regional Cost', component: RegionalCostIntelligence },
    { id: 'ai-quality', label: 'AI Quality', component: AIQualityDashboard },
    { id: 'revision', label: 'Revision Analytics', component: RevisionAnalytics },
    { id: 'portfolio', label: 'Portfolio Analytics', component: PortfolioAnalytics },
    { id: 'team', label: 'Team Analytics', component: TeamAnalytics },
    { id: 'approval', label: 'Approval Analytics', component: ApprovalAnalytics },
    { id: 'audit', label: 'Audit & Compliance', component: AuditComplianceAnalytics },
    { id: 'benchmarking', label: 'Benchmarking', component: BenchmarkingDashboard },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || ExecutiveDashboard

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">Enterprise Analytics</h1>
            <p className="mt-1 text-sm text-gray-500">World-class analytics for construction professionals</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Global Filter Bar */}
        <AnalyticsFilterBar
          filters={filters}
          onFiltersChange={setFilters}
          organizations={organizations}
          projects={projects}
        />

        {/* Export Buttons */}
        <div className="flex justify-end mb-4 gap-2">
          <button
            onClick={() => handleExport('pdf')}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </button>
          <button
            onClick={() => handleExport('excel')}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Export Excel
          </button>
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </button>
        </div>

        <div className="flex space-x-4 border-b border-gray-200 mb-6">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <ActiveComponent />
      </div>
    </div>
  )
}

export default EnterpriseAnalytics
