import { Moon, Sun } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/clerk-react'
import { useTheme } from '@/hooks/useTheme'
import Container from '@/components/Container'

export default function TopNav() {
  const { isDark, toggleTheme } = useTheme()

  return (
    <header className="fixed inset-x-0 top-0 z-50 h-16">
      <div className="pointer-events-none absolute inset-0 bg-paper/70 backdrop-blur-xl" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-ink/10" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-ink/10" />
      <Container className="relative pointer-events-auto flex h-full items-center justify-between">
        <NavLink to="/" className="group flex items-baseline gap-2">
          <span className="font-display text-lg tracking-tight text-ink">Blueprint Reader</span>
          <span className="text-xs tracking-[0.18em] text-ink/50">
            STUDIO
          </span>
        </NavLink>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={toggleTheme}
            className="group inline-flex h-9 w-9 items-center justify-center rounded-full border border-ink/15 bg-paper/60 text-ink/70 transition hover:bg-paper hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
            aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
          >
            {isDark ? (
              <Sun className="h-4 w-4 transition-transform group-hover:-rotate-12" />
            ) : (
              <Moon className="h-4 w-4 transition-transform group-hover:rotate-12" />
            )}
          </button>
          
          <SignedIn>
            <UserButton afterSignOutUrl="/" />
          </SignedIn>
          
          <SignedOut>
            <SignInButton mode="modal">
              <button className="rounded-full border border-ink/15 bg-paper/60 px-4 py-2 text-sm font-medium text-ink transition hover:bg-paper">
                Sign In
              </button>
            </SignInButton>
          </SignedOut>
        </div>
      </Container>
    </header>
  )
}

