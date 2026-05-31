import { Moon, Sun } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'
import Container from '@/components/Container'

function NavItem({ to, children }: { to: string; children: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'text-sm tracking-wide transition-colors',
          isActive ? 'text-ink' : 'text-ink/70 hover:text-ink',
        )
      }
    >
      {children}
    </NavLink>
  )
}

export default function TopNav() {
  const { isDark, toggleTheme } = useTheme()

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="pointer-events-none absolute inset-0 bg-paper/70 backdrop-blur-xl" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-ink/10" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-ink/10" />
      <Container className="relative pointer-events-auto flex h-16 items-center justify-between">
        <NavLink to="/" className="group flex items-baseline gap-2">
          <span className="font-display text-lg tracking-tight text-ink">Blueprint Reader</span>
          <span className="text-xs tracking-[0.18em] text-ink/50">
            STUDIO
          </span>
        </NavLink>

        <nav className="hidden items-center gap-8 md:flex">
          <NavItem to="/">Home</NavItem>
          <NavItem to="/upload">Upload</NavItem>
          <NavItem to="/about">About</NavItem>
          <NavItem to="/contact">Contact</NavItem>
        </nav>

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
          <NavLink
            to="/upload"
            className="hidden rounded-full bg-ink px-4 py-2 text-sm font-medium text-paper transition hover:-translate-y-px hover:bg-ink/90 md:inline-flex"
          >
            Analyze Blueprint
          </NavLink>
        </div>
      </Container>
    </header>
  )
}

