import { FileUp, Loader2, Sparkles, X, Lock, Plus, FolderOpen, ArrowLeft, LayoutDashboard } from 'lucide-react'
import { useMemo, useRef, useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import { analyzeBlueprint } from '@/api/analyzeBlueprint'
import Container from '@/components/Container'
import { cn } from '@/lib/utils'
import { useAnalysisStore } from '@/stores/useAnalysisStore'
import { useNavigationStore } from '@/stores/useNavigationStore'
import { blueprintFilesApi, projectsApi, API_BASE_URL } from '@/lib/api'

const ACCEPTED = [
  '.pdf',
  '.jpg',
  '.jpeg',
  '.png',
  '.dxf',
  '.dwg',
  '.ifc',
] as const

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(1)} KB`
  const mb = kb / 1024
  return `${mb.toFixed(1)} MB`
}

export default function Upload() {
  const { isLoaded, isSignedIn, getToken } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [projects, setProjects] = useState<any[]>([])
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [showCreateProject, setShowCreateProject] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [loadingProjects, setLoadingProjects] = useState(true)
  const { setCurrentAnalysis, setLastUploadedFileId } = useNavigationStore()

  const status = useAnalysisStore((s) => s.status)
  const errorMessage = useAnalysisStore((s) => s.errorMessage)
  const setProcessing = useAnalysisStore((s) => s.setProcessing)
  const setResult = useAnalysisStore((s) => s.setResult)
  const setError = useAnalysisStore((s) => s.setError)

  const canSubmit = useMemo(() => status !== 'processing' && !!file && isSignedIn, [status, file, isSignedIn])

  // Load projects on mount, and also when page gains focus (so dashboard-created projects appear)
  useEffect(() => {
    if (isLoaded && isSignedIn) {
      loadProjects()
    }
  }, [isLoaded, isSignedIn])

  // Pre-select project from URL query param (e.g., /upload?project=<id>)
  useEffect(() => {
    const projectId = searchParams.get('project')
    if (projectId) setSelectedProject(projectId)
  }, [searchParams])

  // Reload projects whenever the tab/window regains focus
  useEffect(() => {
    const onFocus = () => {
      if (isLoaded && isSignedIn) loadProjects()
    }
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [isLoaded, isSignedIn])

  const loadProjects = async () => {
    try {
      setLoadingProjects(true)
      const projectsData = await projectsApi.list()
      setProjects(projectsData)
    } catch (error) {
      console.error('Failed to load projects:', error)
    } finally {
      setLoadingProjects(false)
    }
  }

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return
    try {
      const newProject = await projectsApi.create({
        name: newProjectName,
        building_type: 'residential',
      })
      setProjects([...projects, newProject])
      setSelectedProject(newProject.id)
      setNewProjectName('')
      setShowCreateProject(false)
    } catch (error) {
      console.error('Failed to create project:', error)
      alert(`Failed to create project: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  async function onSubmit() {
    if (!file) return
    setProcessing(file.name)
    try {
      const token = await getToken()
      const res = await analyzeBlueprint(file, token || undefined)
      setResult(file.name, res)

      // Save the analysis results to database for analytics
      let savedFileId: string | null = null
      try {
        const saveResponse = await fetch(`${API_BASE_URL}/blueprint-files/save-analysis`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            filename: file.name,
            project_id: selectedProject,
            analysis_result: res,
            total_area: res.totals?.total_area || null,
            room_count: res.totals?.room_count || res.rooms?.length || null,
          })
        })
        console.log('Save analysis response status:', saveResponse.status)
        console.log('Save analysis response URL:', `${API_BASE_URL}/blueprint-files/save-analysis`)

        if (!saveResponse.ok) {
          const errorText = await saveResponse.text()
          console.error('Save analysis failed:', saveResponse.status, errorText)
          alert(`Failed to save analysis: ${saveResponse.status} - ${errorText}`)
          return
        }

        const savedData = await saveResponse.json()
        console.log('Analysis saved successfully:', savedData)
        savedFileId = savedData?.id || savedData?.file_id || null

        if (savedFileId) {
          // Store navigation context so other pages can reference this file
          setCurrentAnalysis({
            fileId: savedFileId,
            projectId: selectedProject || undefined,
            fileName: file.name,
            originPath: '/upload',
          })
          setLastUploadedFileId(savedFileId)
        }
      } catch (saveError) {
        console.error('Failed to save analysis to database:', saveError)
        alert('Failed to save analysis to database. Please try again.')
        return
      }

      // Navigate to results with file ID if available (enables back-navigation context)
      navigate(savedFileId ? `/results/${savedFileId}` : '/results')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Analysis failed'
      setError(file.name, message)
    }
  }

  function pickFile() {
    inputRef.current?.click()
  }

  // Redirect to sign in if not authenticated
  if (isLoaded && !isSignedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center p-8">
          <Lock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Authentication Required</h2>
          <p className="text-gray-600 mb-6">Please sign in to upload and analyze blueprints</p>
          <button
            onClick={() => navigate('/sign-in')}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            Sign In
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="pb-16">
      {/* Back navigation breadcrumb */}
      <div className="border-b border-ink/10 bg-paper/80 backdrop-blur-sm sticky top-0 z-10">
        <Container>
          <div className="flex items-center gap-2 py-3 text-sm text-ink/60">
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-1.5 hover:text-ink transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <LayoutDashboard className="h-3.5 w-3.5" />
              Dashboard
            </button>
            <span className="text-ink/30">/</span>
            <span className="text-ink font-medium">Upload Blueprint</span>
          </div>
        </Container>
      </div>
      <Container className="pt-10 md:pt-14">
        <div className="grid gap-10 md:grid-cols-12">
          <div className="space-y-4 md:col-span-5">
            <div className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-paper/60 px-3 py-1 text-xs tracking-[0.2em] text-ink/60">
              <Sparkles className="h-3.5 w-3.5 text-accent" />
              UPLOAD
            </div>
            <h1 className="font-display text-4xl leading-[0.95] tracking-tight md:text-5xl">
              Drop a blueprint.
              <span className="block text-ink/80">Get structured output.</span>
            </h1>
            <p className="max-w-md text-sm leading-relaxed text-ink/70">
              Supported: {ACCEPTED.join(' · ')}. The app sends your file to the analysis API and
              renders the returned JSON as a readable schedule.
            </p>
          </div>

          <div className="md:col-span-7">
            {/* Project Selection */}
            <div className="mb-6 rounded-lg border border-ink/20 bg-paper shadow-sm p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <FolderOpen className="h-4 w-4 text-ink/60" />
                  <span className="text-sm font-medium text-ink">Select Project</span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowCreateProject(true)}
                  className="flex items-center gap-1 text-xs text-accent hover:text-accent/80"
                >
                  <Plus className="h-3 w-3" />
                  Create New
                </button>
              </div>
              {loadingProjects ? (
                <div className="text-sm text-ink/60">Loading projects...</div>
              ) : projects.length === 0 ? (
                <div className="text-sm text-ink/60">
                  No projects yet. <button
                    type="button"
                    onClick={() => setShowCreateProject(true)}
                    className="text-accent hover:underline"
                  >
                    Create your first project
                  </button>
                </div>
              ) : (
                <select
                  value={selectedProject || ''}
                  onChange={(e) => setSelectedProject(e.target.value || null)}
                  className="w-full rounded-lg border border-ink/15 bg-paper-2/30 backdrop-blur-sm px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  <option value="">No project (independent file)</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div
              className={cn(
                'relative rounded-3xl border border-ink/12 bg-paper/60 p-6 shadow-soft',
                dragging && 'border-accent/50 bg-accent/5',
              )}
              onDragEnter={(e) => {
                e.preventDefault()
                setDragging(true)
              }}
              onDragOver={(e) => {
                e.preventDefault()
                setDragging(true)
              }}
              onDragLeave={(e) => {
                e.preventDefault()
                setDragging(false)
              }}
              onDrop={(e) => {
                e.preventDefault()
                setDragging(false)
                const dropped = e.dataTransfer.files?.[0]
                if (dropped) setFile(dropped)
              }}
            >
              <div className="flex flex-col items-center justify-center gap-4 py-10 text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-ink/10 bg-paper-2/60 text-ink">
                  <FileUp className="h-6 w-6" />
                </div>
                <div className="space-y-1">
                  <div className="text-sm font-semibold tracking-tight">Drag and drop a file</div>
                  <div className="text-sm text-ink/65">
                    or{' '}
                    <button
                      type="button"
                      onClick={pickFile}
                      className="font-medium text-ink underline decoration-ink/25 underline-offset-4 hover:decoration-ink/50"
                    >
                      choose from your computer
                    </button>
                  </div>
                </div>
                <input
                  ref={inputRef}
                  type="file"
                  className="hidden"
                  accept={ACCEPTED.join(',')}
                  onChange={(e) => {
                    const picked = e.target.files?.[0]
                    if (picked) setFile(picked)
                  }}
                />
              </div>

              {file && (
                <div className="mt-4 flex items-center justify-between rounded-2xl border border-ink/10 bg-paper/60 px-4 py-4">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium">{file.name}</div>
                    <div className="mt-1 text-xs text-ink/60">
                      {formatBytes(file.size)} · {file.type || 'unknown'}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-ink/10 bg-paper/40 text-ink/70 transition hover:bg-paper hover:text-ink"
                    aria-label="Remove file"
                    disabled={status === 'processing'}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}

              <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <button
                  type="button"
                  onClick={onSubmit}
                  disabled={!canSubmit}
                  className={cn(
                    'inline-flex items-center justify-center gap-2 rounded-full px-5 py-3 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50',
                    canSubmit
                      ? 'bg-ink text-paper hover:-translate-y-px hover:bg-ink/90'
                      : 'cursor-not-allowed border border-ink/10 bg-paper-2/50 text-ink/40',
                  )}
                >
                  {status === 'processing' ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Processing
                    </>
                  ) : (
                    <>
                      Analyze blueprint
                      <Sparkles className="h-4 w-4" />
                    </>
                  )}
                </button>

                <div className="text-xs text-ink/60">
                  {status === 'processing'
                    ? 'This may take a moment for larger drawings.'
                    : 'Results will appear in a dedicated view with exports.'}
                </div>
              </div>

              {status === 'error' && errorMessage && (
                <div className="mt-5 rounded-2xl border border-red-500/25 bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-200">
                  {errorMessage}
                </div>
              )}
            </div>
          </div>
        </div>
      </Container>

      {/* Create Project Modal */}
      {showCreateProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="rounded-lg border border-ink/20 bg-paper shadow-sm p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-ink">Create New Project</h3>
              <button
                type="button"
                onClick={() => setShowCreateProject(false)}
                className="text-ink/60 hover:text-ink"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Project Name</label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="Enter project name"
                  className="w-full rounded-lg border border-ink/15 bg-paper-2/50 px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowCreateProject(false)}
                  className="px-4 py-2 rounded-lg border border-ink/15 bg-paper-2/50 text-sm text-ink hover:bg-paper-2"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleCreateProject}
                  disabled={!newProjectName.trim()}
                  className="px-4 py-2 rounded-lg bg-accent text-paper text-sm font-medium hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Project
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}