import React, { useState, useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface PortfolioData {
  totalProjects: number
  totalArea: number
  totalBOQValue: number
  avgCostPerSqFt: number
  projectsByType: Array<{name: string, value: number}>
  projectsByStatus: Array<{status: string, count: number}>
  monthlyTrends: Array<{month: string, projects: number, area: number, cost: number}>
  projectsByRegion: Array<{region: string, count: number}>
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export default function EnterpriseDashboard() {
  const { isLoaded, isSignedIn } = useAuth()
  const [data, setData] = useState<PortfolioData | null>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    if (isLoaded && isSignedIn) {
      loadAnalytics()
    }
  }, [isLoaded, isSignedIn])
  
  const loadAnalytics = async () => {
    try {
      setLoading(true)
      // This would call the analytics API
      // For now, we'll simulate the data
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setData({
        totalProjects: 24,
        totalArea: 125000,
        totalBOQValue: 18750000,
        avgCostPerSqFt: 150,
        projectsByType: [
          { name: 'Residential', value: 12 },
          { name: 'Commercial', value: 8 },
          { name: 'Industrial', value: 4 }
        ],
        projectsByStatus: [
          { status: 'Active', count: 15 },
          { status: 'In Progress', count: 6 },
          { status: 'Completed', count: 3 }
        ],
        monthlyTrends: [
          { month: 'Jan', projects: 2, area: 8000, cost: 1200000 },
          { month: 'Feb', projects: 3, area: 12000, cost: 1800000 },
          { month: 'Mar', projects: 4, area: 15000, cost: 2250000 },
          { month: 'Apr', projects: 5, area: 18000, cost: 2700000 },
          { month: 'May', projects: 6, area: 22000, cost: 3300000 },
          { month: 'Jun', projects: 4, area: 15000, cost: 2250000 }
        ],
        projectsByRegion: [
          { region: 'Mumbai', count: 10 },
          { region: 'Delhi', count: 8 },
          { region: 'Bangalore', count: 6 }
        ]
      })
    } catch (error) {
      console.error('Failed to load analytics', error)
    } finally {
      setLoading(false)
    }
  }
  
  if (!isLoaded || !isSignedIn) {
    return <div className="p-8">Loading...</div>
  }
  
  if (loading) {
    return <div className="p-8">Loading analytics...</div>
  }
  
  if (!data) {
    return <div className="p-8">No data available</div>
  }
  
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold mb-8">Enterprise Analytics Dashboard</h1>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Projects"
          value={data.totalProjects}
          change="+12%"
          trend="up"
        />
        <MetricCard
          title="Total Area"
          value={`${data.totalArea.toLocaleString()} sq ft`}
          change="+8%"
          trend="up"
        />
        <MetricCard
          title="Total BOQ Value"
          value={`₹${(data.totalBOQValue / 1000000).toFixed(1)}M`}
          change="+15%"
          trend="up"
        />
        <MetricCard
          title="Avg Cost/Sq Ft"
          value={`₹${data.avgCostPerSqFt.toFixed(0)}`}
          change="+3%"
          trend="up"
        />
      </div>
      
      {/* Charts */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-xl p-6 border">
          <h3 className="font-semibold mb-4">Projects by Building Type</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data.projectsByType}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {data.projectsByType.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        
        <div className="bg-white rounded-xl p-6 border">
          <h3 className="font-semibold mb-4">Projects by Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.projectsByStatus}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="status" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="bg-white rounded-xl p-6 border mb-8">
        <h3 className="font-semibold mb-4">Monthly Trends</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.monthlyTrends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="projects" stroke="#3b82f6" name="Projects" />
            <Line type="monotone" dataKey="area" stroke="#10b981" name="Area (sq ft)" />
            <Line type="monotone" dataKey="cost" stroke="#f59e0b" name="Cost (₹)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div className="bg-white rounded-xl p-6 border">
        <h3 className="font-semibold mb-4">Projects by Region</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data.projectsByRegion} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="region" type="category" width={100} />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function MetricCard({ title, value, change, trend }: {title: string, value: string | number, change: string, trend: 'up' | 'down'}) {
  return (
    <div className="bg-white rounded-xl p-6 border">
      <div className="text-sm text-gray-500 mb-2">{title}</div>
      <div className="text-3xl font-bold text-gray-900 mb-2">{value}</div>
      <div className={`text-sm ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
        {change} from last month
      </div>
    </div>
  )
}
