import { NavLink } from 'react-router-dom'
import Container from '@/components/Container'

export default function Footer() {
  return (
    <footer className="border-t border-ink/10 py-10">
      <Container className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <div className="font-display text-xl tracking-tight">Blueprint Reader</div>
          <div className="max-w-md text-sm leading-relaxed text-ink/70">
            Blueprint intelligence for fast takeoffs, clear room schedules, and BOQ-ready outputs.
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-ink/70">
          <NavLink to="/upload" className="hover:text-ink">
            Upload
          </NavLink>
          <NavLink to="/about" className="hover:text-ink">
            About
          </NavLink>
          <NavLink to="/contact" className="hover:text-ink">
            Contact
          </NavLink>
          <span className="text-ink/45">© {new Date().getFullYear()}</span>
        </div>
      </Container>
    </footer>
  )
}

