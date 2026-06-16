const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

console.log('API_BASE_URL:', API_BASE_URL)

export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('__clerk_db_jwt')
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers,
  }

  const fullUrl = `${API_BASE_URL}${url}`
  console.log(`API Request: ${fullUrl}`, { method: options.method, hasToken: !!token })

  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers,
    })

    console.log(`API Response: ${response.status} ${response.statusText}`)

    if (!response.ok) {
      const errorText = await response.text().catch(() => '')
      console.error(`API Error: ${response.status} - ${errorText}`)
      throw new Error(`API error: ${response.status} - ${errorText}`)
    }

    return response.json()
  } catch (error) {
    console.error('Fetch error:', error)
    throw error
  }
}

// Organizations
export const organizationsApi = {
  list: () => fetchWithAuth('/organizations/'),
  get: (id: string) => fetchWithAuth(`/organizations/${id}/`),
  create: (data: any) => fetchWithAuth('/organizations/', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  update: (id: string, data: any) => fetchWithAuth(`/organizations/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
}

// Projects
export const projectsApi = {
  list: (organizationId?: string) => fetchWithAuth(`/projects/${organizationId ? `?organization_id=${organizationId}` : ''}`),
  get: (id: string) => fetchWithAuth(`/projects/${id}/`),
  create: (data: any) => fetchWithAuth('/projects/', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  update: (id: string, data: any) => fetchWithAuth(`/projects/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  delete: (id: string) => fetchWithAuth(`/projects/${id}/`, {
    method: 'DELETE',
  }),
}

// Analysis
export const analysisApi = {
  start: (data: any) => fetchWithAuth('/analysis/start', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  get: (id: string) => fetchWithAuth(`/analysis/${id}`),
  list: (projectId: string) => fetchWithAuth(`/analysis/project/${projectId}`),
}

// Files
export const filesApi = {
  upload: (projectId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_id', projectId)
    
    const token = localStorage.getItem('__clerk_db_jwt')
    return fetch(`${API_BASE_URL}/files/upload`, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: formData,
    }).then(res => res.json())
  },
}

// Blueprint Files
export const blueprintFilesApi = {
  list: (projectId?: string, limit: number = 10) => fetchWithAuth(`/blueprint-files/${projectId ? `?project_id=${projectId}&limit=${limit}` : `?limit=${limit}`}`),
  get: (id: string) => fetchWithAuth(`/blueprint-files/${id}`),
  create: (data: any) => {
    // If data is FormData (for file upload), don't stringify
    if (data instanceof FormData) {
      const token = localStorage.getItem('__clerk_db_jwt')
      return fetch(`${API_BASE_URL}/blueprint-files/`, {
        method: 'POST',
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: data,
      }).then(res => res.json())
    }
    return fetchWithAuth('/blueprint-files/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
  analyze: (id: string) => fetchWithAuth(`/blueprint-files/${id}/analyze`, {
    method: 'POST',
  }),
  delete: (id: string) => fetchWithAuth(`/blueprint-files/${id}`, {
    method: 'DELETE',
  }),
}

// Floor Comparison API
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

interface FloorComparisonRequest {
  project_id: string
  file_a_id: string
  file_b_id: string
  floor_a_label?: string
  floor_b_label?: string
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

export const floorComparisonApi = {
  compare: (request: FloorComparisonRequest) => fetchWithAuth('/floor-comparison/compare', {
    method: 'POST',
    body: JSON.stringify({
      floor_a_id: request.file_a_id,
      floor_b_id: request.file_b_id,
    }),
  }),
  list: (projectId: string) => fetchWithAuth(`/floor-comparison/project/${projectId}`),
  get: (id: string) => fetchWithAuth(`/floor-comparison/${id}`),
}

// Public Shares API
interface PublicShareCreate {
  blueprint_file_id: string
  title?: string
  description?: string
  password?: string
  expires_in_days?: number
}

interface PublicShare {
  id: string
  share_token: string
  blueprint_file_id: string
  project_id: string
  title: string | null
  description: string | null
  has_password: boolean
  expires_at: string | null
  view_count: number
  last_viewed_at: string | null
  is_active: boolean
  created_at: string
  share_url: string
}

interface PublicShareView {
  title: string | null
  description: string | null
  filename: string
  analysis_result: any
  total_area: number | null
  room_count: number | null
  boq_total: number | null
  viewed_at: string
}

export const publicSharesApi = {
  create: (data: PublicShareCreate) => fetchWithAuth('/public-shares/', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  list: (projectId: string) => fetchWithAuth(`/public-shares/project/${projectId}`),
  get: (id: string) => fetchWithAuth(`/public-shares/${id}`),
  delete: (id: string) => fetchWithAuth(`/public-shares/${id}`, {
    method: 'DELETE',
  }),
  deactivate: (id: string) => fetchWithAuth(`/public-shares/${id}/deactivate`, {
    method: 'PATCH',
  }),
  // Public endpoint (no auth required)
  viewPublic: (token: string, password?: string) => {
    const url = password
      ? `/public-shares/public/${token}?password=${encodeURIComponent(password)}`
      : `/public-shares/public/${token}`
    return fetch(`${API_BASE_URL}${url}`).then(res => res.json())
  },
}

// Cost Benchmarking API
interface CostBenchmarkCreate {
  project_id: string
  category: string
  metric_name: string
  your_value: number
  your_unit?: string
  benchmark_value: number
  benchmark_unit?: string
  benchmark_source?: string
  region?: string
  building_type?: string
  project_size_category?: string
}

interface CostBenchmark {
  id: string
  project_id: string
  category: string
  metric_name: string
  your_value: number
  your_unit: string | null
  benchmark_value: number
  benchmark_unit: string | null
  benchmark_source: string | null
  variance_percentage: number | null
  variance_status: string | null
  region: string | null
  building_type: string | null
  project_size_category: string | null
  created_at: string
}

interface IndustryCostData {
  id: string
  category: string
  metric_name: string
  benchmark_value: number
  unit: string | null
  min_value: number | null
  max_value: number | null
  percentile_25: number | null
  percentile_75: number | null
  region: string | null
  building_type: string | null
  project_size: string | null
  source: string | null
  source_year: number | null
}

interface ProjectComparison {
  project_id: string
  project_name: string
  metrics: Array<{
    metric: string
    your_value: number
    benchmark_value: number
    variance_percentage: number
    status: string
  }>
}

export const costBenchmarkApi = {
  create: (data: CostBenchmarkCreate) => fetchWithAuth('/cost-benchmark/', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  list: (projectId: string) => fetchWithAuth(`/cost-benchmark/project/${projectId}`),
  getIndustryData: (filters?: { category?: string; region?: string; building_type?: string; project_size?: string }) => {
    const params = new URLSearchParams()
    if (filters?.category) params.append('category', filters.category)
    if (filters?.region) params.append('region', filters.region)
    if (filters?.building_type) params.append('building_type', filters.building_type)
    if (filters?.project_size) params.append('project_size', filters.project_size)
    const queryString = params.toString()
    return fetchWithAuth(`/cost-benchmark/industry-data${queryString ? '?' + queryString : ''}`)
  },
  compare: (projectId: string) => fetchWithAuth(`/cost-benchmark/compare/${projectId}`),
  delete: (id: string) => fetchWithAuth(`/cost-benchmark/${id}`, {
    method: 'DELETE',
  }),
}


