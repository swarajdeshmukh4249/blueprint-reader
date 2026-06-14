import { AlertCircle, Home, ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import Container from '@/components/Container'

interface ErrorPageProps {
  code?: number
  title?: string
  message?: string
  showBackButton?: boolean
}

export default function ErrorPage({ 
  code = 500, 
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again later.',
  showBackButton = true
}: ErrorPageProps) {
  const navigate = useNavigate()

  const handleGoHome = () => {
    navigate('/')
  }

  const handleGoBack = () => {
    navigate(-1)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper">
      <Container className="text-center">
        <div className="max-w-md mx-auto">
          <div className="flex justify-center mb-6">
            <div className="h-24 w-24 rounded-full bg-red-100 flex items-center justify-center">
              <AlertCircle className="h-12 w-12 text-red-600" />
            </div>
          </div>
          
          <h1 className="font-display text-6xl tracking-tight text-ink mb-2">
            {code}
          </h1>
          
          <h2 className="font-display text-2xl tracking-tight text-ink mb-3">
            {title}
          </h2>
          
          <p className="text-sm text-ink/70 mb-8">
            {message}
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            {showBackButton && (
              <button
                onClick={handleGoBack}
                className="flex items-center justify-center gap-2 rounded-full border border-ink/15 bg-paper px-6 py-3 text-sm font-medium text-ink transition hover:bg-paper-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Go Back
              </button>
            )}
            
            <button
              onClick={handleGoHome}
              className="flex items-center justify-center gap-2 rounded-full bg-ink px-6 py-3 text-sm font-medium text-paper transition hover:bg-ink/90"
            >
              <Home className="h-4 w-4" />
              Go to Dashboard
            </button>
          </div>
        </div>
      </Container>
    </div>
  )
}
