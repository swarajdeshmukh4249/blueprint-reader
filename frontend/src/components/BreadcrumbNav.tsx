import { ChevronRight, Home, FileText, BarChart3, Ruler, Eye } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useNavigationStore } from '@/stores/useNavigationStore'

interface BreadcrumbItem {
  label: string
  path: string
  icon?: React.ElementType
}

export default function BreadcrumbNav() {
  const navigate = useNavigate()
  const location = useLocation()
  const { currentAnalysis, clearCurrentAnalysis } = useNavigationStore()

  const getBreadcrumbs = (): BreadcrumbItem[] => {
    const breadcrumbs: BreadcrumbItem[] = [
      { label: 'Home', path: '/', icon: Home }
    ]

    // Add current analysis context if available
    if (currentAnalysis) {
      breadcrumbs.push({
        label: currentAnalysis.fileName || 'Analysis',
        path: `/results/${currentAnalysis.fileId}`,
        icon: FileText
      })
    }

    // Add current page
    const pathSegments = location.pathname.split('/').filter(Boolean)
    const currentPage = pathSegments[pathSegments.length - 1]

    if (currentPage && currentPage !== 'results') {
      const pageLabels: Record<string, string> = {
        'dashboard': 'Dashboard',
        'upload': 'Upload',
        'scale-calibration': 'Scale Calibration',
        'analytics': 'Analytics',
        'viewer': 'Viewer',
        'project': 'Project',
      }

      const pageIcons: Record<string, React.ElementType> = {
        'dashboard': BarChart3,
        'upload': FileText,
        'scale-calibration': Ruler,
        'analytics': BarChart3,
        'viewer': Eye,
      }

      breadcrumbs.push({
        label: pageLabels[currentPage] || currentPage.charAt(0).toUpperCase() + currentPage.slice(1),
        path: location.pathname,
        icon: pageIcons[currentPage]
      })
    }

    return breadcrumbs
  }

  const breadcrumbs = getBreadcrumbs()

  const handleBreadcrumbClick = (path: string, index: number) => {
    // If clicking the analysis breadcrumb and we're going back to results, clear context
    if (index === 1 && currentAnalysis && path.includes('/results')) {
      clearCurrentAnalysis()
    }
    navigate(path)
  }

  if (breadcrumbs.length <= 1) return null

  return (
    <nav className="flex items-center space-x-2 text-sm bg-paper border-b border-ink/10 px-4 py-3">
      {breadcrumbs.map((item, index) => (
        <div key={item.path} className="flex items-center">
          {index > 0 && (
            <ChevronRight className="w-4 h-4 text-ink/40 mx-2" />
          )}
          <button
            onClick={() => handleBreadcrumbClick(item.path, index)}
            className={`flex items-center gap-1.5 hover:text-accent transition-colors ${index === breadcrumbs.length - 1
              ? 'text-ink font-medium cursor-default'
              : 'text-ink/60'
              }`}
            disabled={index === breadcrumbs.length - 1}
          >
            {item.icon && (() => {
              const Icon = item.icon as any
              return <Icon className="w-4 h-4" />
            })()}
            <span>{item.label}</span>
          </button>
        </div>
      ))}
    </nav>
  )
}