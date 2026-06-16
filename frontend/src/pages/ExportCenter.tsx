import { SignedIn } from '@clerk/clerk-react'
import { Download, FileText, FileSpreadsheet, Image as ImageIcon, Package, Search } from 'lucide-react'
import Container from '@/components/Container'
import { useState, useEffect } from 'react'
import { blueprintFilesApi, projectsApi } from '@/lib/api'
import { useAuth } from '@clerk/clerk-react'

export default function ExportCenter() {
  const { getToken } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFormat, setSelectedFormat] = useState('all')
  const [blueprintFiles, setBlueprintFiles] = useState<any[]>([])
  const [projects, setProjects] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  // Refresh data when component mounts or when navigating to it
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [filesData, projectsData] = await Promise.all([
        blueprintFilesApi.list(),
        projectsApi.list()
      ])
      setBlueprintFiles(filesData)
      setProjects(projectsData)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const exports = blueprintFiles.filter(file => file.status === 'analyzed').map(file => {
    const project = projects.find(p => p.id === file.project_id)
    return {
      id: file.id,
      name: file.filename,
      type: 'pdf', // Default to PDF for analyzed files
      size: file.total_area ? `${(file.total_area * 0.001).toFixed(2)} MB` : 'Unknown',
      date: file.analyzed_at ? new Date(file.analyzed_at).toISOString().split('T')[0] : new Date(file.created_at).toISOString().split('T')[0],
      project: project?.name || 'Unknown Project'
    }
  })

  const filteredExports = exports.filter(exp => {
    const matchesSearch = exp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         exp.project.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFormat = selectedFormat === 'all' || exp.type === selectedFormat
    return matchesSearch && matchesFormat
  })

  const getIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return <FileText className="h-5 w-5 text-red-500" />
      case 'xlsx':
        return <FileSpreadsheet className="h-5 w-5 text-green-500" />
      case 'png':
        return <ImageIcon className="h-5 w-5 text-blue-500" />
      case 'csv':
        return <FileSpreadsheet className="h-5 w-5 text-green-600" />
      case 'zip':
        return <Package className="h-5 w-5 text-yellow-500" />
      default:
        return <FileText className="h-5 w-5 text-ink/50" />
    }
  }

  const getFormatLabel = (type: string) => {
    switch (type) {
      case 'pdf': return 'PDF'
      case 'xlsx': return 'Excel'
      case 'png': return 'Image'
      case 'csv': return 'CSV'
      case 'zip': return 'ZIP'
      default: return type.toUpperCase()
    }
  }

  const handleExport = async (fileId: string, format: string) => {
    try {
      setExporting(fileId)
      const token = await getToken()
      
      // Get the file details
      const file = blueprintFiles.find(f => f.id === fileId)
      if (!file || !file.analysis_result) {
        alert('No analysis data available for export')
        return
      }

      const analysisResult = file.analysis_result
      let content = ''
      let mimeType = ''
      let filename = `${file.filename.replace(/\.[^/.]+$/, '')}_${format}`

      switch (format) {
        case 'csv':
          // Export as CSV
          const rooms = analysisResult.rooms || []
          const headers = ['name', 'area', 'unit', 'confidence']
          const csvRows = [headers.join(',')]
          rooms.forEach((room: any) => {
            csvRows.push([room.name, room.area, room.unit, room.confidence].join(','))
          })
          content = csvRows.join('\n')
          mimeType = 'text/csv'
          filename += '.csv'
          break

        case 'xlsx':
          // For Excel, we'll create a simple CSV for now (would need a library for true Excel)
          const boq = analysisResult.boq || []
          const boqHeaders = ['item', 'quantity', 'rate', 'unit', 'amount']
          const boqRows = [boqHeaders.join(',')]
          boq.forEach((item: any) => {
            boqRows.push([item.item, item.quantity, item.rate, item.unit, item.amount].join(','))
          })
          content = boqRows.join('\n')
          mimeType = 'text/csv'
          filename += '_boq.csv'
          break

        case 'pdf':
          // For PDF, we'll create a simple text report for now
          const report = `
Blueprint Analysis Report
========================
File: ${file.filename}
Date: ${new Date().toLocaleString()}

Summary:
-------
Total Area: ${analysisResult.total_area || 'N/A'}
Room Count: ${analysisResult.room_count || analysisResult.rooms?.length || 0}

Rooms:
------
${(analysisResult.rooms || []).map((r: any) => 
  `- ${r.name}: ${r.area} ${r.unit || ''} (confidence: ${Math.round((r.confidence || 0) * 100)}%)
`).join('\n')}

Bill of Quantities:
------------------
${(analysisResult.boq || []).map((b: any) => 
  `- ${b.item}: ${b.quantity} ${b.unit || ''} @ ${b.rate} = ${b.amount}
`).join('\n')}
          `
          content = report
          mimeType = 'text/plain'
          filename += '.txt'
          break

        default:
          content = JSON.stringify(analysisResult, null, 2)
          mimeType = 'application/json'
          filename += '.json'
      }

      // Create download
      const blob = new Blob([content], { type: mimeType })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)

    } catch (error) {
      console.error('Export failed:', error)
      alert('Export failed. Please try again.')
    } finally {
      setExporting(null)
    }
  }

  return (
    <SignedIn>
      <div className="min-h-screen">
        <Container className="py-8">
          <div className="mb-8">
            <h1 className="font-display text-3xl tracking-tight text-ink">Export Center</h1>
            <p className="mt-2 text-sm text-ink/70">
              Download and manage your exported files and reports
            </p>
          </div>

          {/* Search and Filter */}
          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink/50" />
              <input
                type="text"
                placeholder="Search exports..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-ink/15 bg-paper pl-10 pr-4 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
            </div>

            <select
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value)}
              className="rounded-lg border border-ink/15 bg-paper px-4 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            >
              <option value="all">All Formats</option>
              <option value="pdf">PDF</option>
              <option value="xlsx">Excel</option>
              <option value="png">Image</option>
              <option value="csv">CSV</option>
              <option value="zip">ZIP</option>
            </select>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-ink/10 border-t-accent mx-auto" />
              <p className="mt-4 text-sm text-ink/70">Loading exports...</p>
            </div>
          ) : (
            <>
              {/* Export Grid */}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {filteredExports.map((exp) => (
              <div
                key={exp.id}
                className="rounded-lg border border-ink/10 bg-paper-2/50 p-4 transition hover:border-accent/30 hover:shadow-lg"
              >
                <div className="flex items-start justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-paper">
                    {getIcon(exp.type)}
                  </div>
                  <button 
                    onClick={() => handleExport(exp.id, exp.type)}
                    disabled={exporting === exp.id}
                    className="rounded-full border border-ink/15 bg-paper p-2 text-ink/70 transition hover:bg-accent hover:text-paper disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {exporting === exp.id ? (
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-ink/10 border-t-accent" />
                    ) : (
                      <Download className="h-4 w-4" />
                    )}
                  </button>
                </div>

                <div className="mt-4">
                  <h3 className="text-sm font-medium text-ink line-clamp-2">{exp.name}</h3>
                  <p className="mt-1 text-xs text-ink/50">{exp.project}</p>
                </div>

                <div className="mt-4 flex items-center justify-between text-xs text-ink/50">
                  <span>{getFormatLabel(exp.type)}</span>
                  <span>{exp.size}</span>
                </div>

                <div className="mt-2 text-xs text-ink/40">{exp.date}</div>
              </div>
            ))}
          </div>

          {filteredExports.length === 0 && (
            <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-12 text-center">
              <Download className="mx-auto h-12 w-12 text-ink/30" />
              <h3 className="mt-4 font-display text-lg tracking-tight text-ink">No exports found</h3>
              <p className="mt-2 text-sm text-ink/70">
                {searchQuery || selectedFormat !== 'all'
                  ? 'Try adjusting your search or filters'
                  : 'Your exported files will appear here'}
              </p>
            </div>
          )}
            </>
          )}
        </Container>
      </div>
    </SignedIn>
  )
}
