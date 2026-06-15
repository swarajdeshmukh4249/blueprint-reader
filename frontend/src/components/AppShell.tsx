import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Footer from '@/components/Footer'
import TopNav from '@/components/TopNav'
import SideNav from '@/components/SideNav'
import CommandPalette from '@/components/CommandPalette'

export default function AppShell() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className="min-h-dvh text-ink selection:bg-accent/25 selection:text-ink">
      <TopNav />
      <div className="flex">
        <SideNav onCollapsedChange={setSidebarCollapsed} />
        <main className={`flex-1 pt-20 lg:pt-16 min-h-screen transition-all duration-300 ${sidebarCollapsed ? 'lg:ml-0' : 'lg:ml-64'}`}>
          <Outlet />
        </main>
      </div>
      <Footer />
      <CommandPalette />
    </div>
  )
}
