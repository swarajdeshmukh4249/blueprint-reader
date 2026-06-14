import { Outlet } from 'react-router-dom'
import Footer from '@/components/Footer'
import TopNav from '@/components/TopNav'
import SideNav from '@/components/SideNav'
import CommandPalette from '@/components/CommandPalette'

export default function AppShell() {
  return (
    <div className="min-h-dvh text-ink selection:bg-accent/25 selection:text-ink">
      <TopNav />
      <div className="flex">
        <SideNav />
        <main className="flex-1 pt-20 lg:pt-16 lg:ml-64 min-h-screen">
          <Outlet />
        </main>
      </div>
      <Footer />
      <CommandPalette />
    </div>
  )
}
