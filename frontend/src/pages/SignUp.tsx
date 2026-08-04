import { SignUp } from '@clerk/clerk-react'
import Container from '@/components/Container'

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <Container className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Create Account</h1>
          <p className="mt-2 text-sm text-ink/70">
            Start analyzing blueprints with AI
          </p>
        </div>
        <SignUp 
          signInUrl="/sign-in"
          redirectUrl="/dashboard"
        />
      </Container>
    </div>
  )
}
