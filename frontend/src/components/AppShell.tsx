import { Outlet } from 'react-router-dom'
import Footer from '@/components/Footer'
import TopNav from '@/components/TopNav'
import CommandPalette from '@/components/CommandPalette'

export default function AppShell() {
  return (
    <div className="min-h-dvh text-ink selection:bg-accent/25 selection:text-ink">
      <TopNav />
      <main className="pt-24">
        <Outlet />
      </main>
      <Footer />
      <CommandPalette />
    </div>
  )
}
