import { Component, ReactNode } from 'react'
import { AlertCircle, RefreshCw, Home } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />
    }

    return this.props.children
  }
}

function ErrorFallback({ error }: { error: Error | null }) {
  const navigate = useNavigate()

  const handleReload = () => {
    window.location.reload()
  }

  const handleGoHome = () => {
    navigate('/')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper">
      <div className="max-w-md w-full mx-4">
        <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-8 text-center">
          <div className="flex justify-center mb-4">
            <div className="h-16 w-16 rounded-full bg-red-100 flex items-center justify-center">
              <AlertCircle className="h-8 w-8 text-red-600" />
            </div>
          </div>
          
          <h1 className="font-display text-2xl tracking-tight text-ink mb-2">
            Something went wrong
          </h1>
          
          <p className="text-sm text-ink/70 mb-6">
            {error?.message || 'An unexpected error occurred. Please try again.'}
          </p>

          <div className="flex flex-col gap-3">
            <button
              onClick={handleReload}
              className="flex items-center justify-center gap-2 rounded-full bg-ink px-6 py-3 text-sm font-medium text-paper transition hover:bg-ink/90"
            >
              <RefreshCw className="h-4 w-4" />
              Try Again
            </button>
            
            <button
              onClick={handleGoHome}
              className="flex items-center justify-center gap-2 rounded-full border border-ink/15 bg-paper px-6 py-3 text-sm font-medium text-ink transition hover:bg-paper-2"
            >
              <Home className="h-4 w-4" />
              Go to Dashboard
            </button>
          </div>

          {error && process.env.NODE_ENV === 'development' && (
            <details className="mt-6 text-left">
              <summary className="text-xs font-medium text-ink/50 cursor-pointer">
                Error Details
              </summary>
              <pre className="mt-2 text-xs text-ink/40 overflow-auto bg-paper p-3 rounded">
                {error.stack}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  )
}
