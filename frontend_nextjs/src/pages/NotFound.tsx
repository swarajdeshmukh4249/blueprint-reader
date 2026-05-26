import { NavLink } from 'react-router-dom'
import Container from '@/components/Container'

export default function NotFound() {
  return (
    <Container className="pt-12 pb-16">
      <div className="rounded-3xl border border-ink/10 bg-paper/60 p-10 text-center shadow-soft">
        <div className="font-display text-4xl tracking-tight">404</div>
        <div className="mt-2 text-sm text-ink/70">That page does not exist.</div>
        <NavLink
          to="/"
          className="mt-6 inline-flex rounded-full bg-ink px-5 py-3 text-sm font-medium text-paper transition hover:-translate-y-px hover:bg-ink/90"
        >
          Back to Home
        </NavLink>
      </div>
    </Container>
  )
}

