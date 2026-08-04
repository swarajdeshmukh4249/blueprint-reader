import { SignIn } from '@clerk/clerk-react'
import Container from '@/components/Container'

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <Container className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Sign In</h1>
          <p className="mt-2 text-sm text-ink/70">
            Access your Blueprint Reader account
          </p>
        </div>
        <SignIn 
          signUpUrl="/sign-up"
          redirectUrl="/dashboard"
        />
      </Container>
    </div>
  )
}
