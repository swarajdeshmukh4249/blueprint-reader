import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Footer from '@/components/Footer'
import TopNav from '@/components/TopNav'
import SideNav from '@/components/SideNav'
import CommandPalette from '@/components/CommandPalette'
import ThemeToggle from '@/components/ThemeToggle'
import SimpleCube from '@/components/SimpleCube'
import Blueprint3DBackground from '@/components/Blueprint3DBackground'

export default function AppShell() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className="relative min-h-dvh text-ink selection:bg-accent/25 selection:text-ink">

      {/* 3D Blueprint Background */}
      <div className="pointer-events-none">
        <Blueprint3DBackground />
      </div>

      {/* Theme Toggle */}
      <ThemeToggle />

      {/* Floating Cube */}
      <div className="fixed bottom-4 right-4 z-10 pointer-events-none opacity-40 mix-blend-screen">
        <SimpleCube />
      </div>

      {/* Navigation */}
      <TopNav />

      <div className="relative z-10 flex">
        <SideNav onCollapsedChange={setSidebarCollapsed} />

        <main
          className={`flex-1 pt-20 lg:pt-16 min-h-screen transition-all duration-300 ${
            sidebarCollapsed ? 'lg:ml-0' : 'lg:ml-64'
          }`}
        >
          <Outlet />
        </main>
      </div>

      <Footer />

      <CommandPalette />
    </div>
  )
}