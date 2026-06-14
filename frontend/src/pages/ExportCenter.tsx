import { SignedIn } from '@clerk/clerk-react'
import { Download, FileText, FileSpreadsheet, Image as ImageIcon, Package, Search } from 'lucide-react'
import Container from '@/components/Container'
import { useState, useEffect } from 'react'
import { blueprintFilesApi, projectsApi } from '@/lib/api'

export default function ExportCenter() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFormat, setSelectedFormat] = useState('all')
  const [blueprintFiles, setBlueprintFiles] = useState<any[]>([])
  const [projects, setProjects] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

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
                  <button className="rounded-full border border-ink/15 bg-paper p-2 text-ink/70 transition hover:bg-accent hover:text-paper">
                    <Download className="h-4 w-4" />
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

          {/* Export Options */}
          <div className="mt-8 rounded-lg border border-ink/10 bg-paper-2/50 p-6">
            <h2 className="font-display text-xl tracking-tight text-ink">Export Options</h2>
            <p className="mt-1 text-sm text-ink/70">
              Create new exports from your analysis results
            </p>

            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <ExportOption
                title="PDF Report"
                description="Complete analysis report in PDF format"
                icon={<FileText className="h-6 w-6 text-red-500" />}
              />
              <ExportOption
                title="Excel BOQ"
                description="Bill of Quantities in Excel format"
                icon={<FileSpreadsheet className="h-6 w-6 text-green-500" />}
              />
              <ExportOption
                title="Image Export"
                description="Blueprint images in high resolution"
                icon={<ImageIcon className="h-6 w-6 text-blue-500" />}
              />
              <ExportOption
                title="Complete Package"
                description="All files in a single ZIP archive"
                icon={<Package className="h-6 w-6 text-yellow-500" />}
              />
            </div>
          </div>
            </>
          )}
        </Container>
      </div>
    </SignedIn>
  )
}

function ExportOption({ title, description, icon }: { title: string; description: string; icon: React.ReactNode }) {
  return (
    <button className="flex flex-col items-start rounded-lg border border-ink/15 bg-paper p-4 text-left transition hover:border-accent/30 hover:shadow-md">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-paper-2">
        {icon}
      </div>
      <div className="mt-3">
        <h3 className="text-sm font-medium text-ink">{title}</h3>
        <p className="mt-1 text-xs text-ink/70">{description}</p>
      </div>
    </button>
  )
}
