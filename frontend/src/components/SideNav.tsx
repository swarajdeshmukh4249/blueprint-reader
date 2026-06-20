import { NavLink } from 'react-router-dom'
import { SignedIn, SignedOut, UserButton } from '@clerk/clerk-react'
import { 
  Home, 
  Upload, 
  BarChart3, 
  Settings, 
  Download, 
  HelpCircle, 
  Users,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  Ruler,
  FileText
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

function NavItem({ to, icon: Icon, children }: { to: string; icon: any; children: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
          isActive 
            ? 'bg-accent/10 text-accent' 
            : 'text-ink/70 hover:bg-ink/5 hover:text-ink'
        )
      }
    >
      <Icon className="h-4 w-4" />
      {children}
    </NavLink>
  )
}

interface SideNavProps {
  onCollapsedChange?: (collapsed: boolean) => void
}

export default function SideNav({ onCollapsedChange }: SideNavProps) {
  const [collapsed, setCollapsed] = useState(false)
  const [desktopCollapsed, setDesktopCollapsed] = useState(false)

  const handleDesktopToggle = () => {
    const newCollapsed = !desktopCollapsed
    setDesktopCollapsed(newCollapsed)
    onCollapsedChange?.(newCollapsed)
  }

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="lg:hidden fixed top-20 left-4 z-40 inline-flex h-10 w-10 items-center justify-center rounded-full border border-ink/15 bg-paper/60 text-ink/70 transition hover:bg-paper hover:text-ink shadow-lg"
        aria-label="Toggle menu"
      >
        {collapsed ? <Menu className="h-5 w-5" /> : <X className="h-5 w-5" />}
      </button>

      {/* Desktop Toggle Button - shown when sidebar is collapsed */}
      {desktopCollapsed && (
        <button
          onClick={handleDesktopToggle}
          className="hidden lg:flex fixed top-20 left-4 z-40 h-8 w-8 items-center justify-center rounded-lg border border-ink/15 bg-paper/60 text-ink/70 transition hover:bg-paper hover:text-ink shadow-lg"
          aria-label="Toggle sidebar"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      )}

      {/* Side Navigation */}
      <aside 
        className={cn(
          'fixed left-0 top-16 bottom-0 z-30 w-64 bg-paper/95 backdrop-blur-xl border-r border-ink/10 transition-all duration-300 ease-in-out',
          collapsed ? '-translate-x-full' : 'translate-x-0',
          desktopCollapsed ? 'lg:-translate-x-full lg:opacity-0' : 'lg:translate-x-0 lg:opacity-100'
        )}
      >
        <nav className="flex h-full flex-col p-4">
          {/* Collapse Button */}
          <button
            onClick={handleDesktopToggle}
            className="hidden lg:flex mb-4 h-8 w-8 items-center justify-center rounded-lg border border-ink/15 bg-paper/60 text-ink/70 transition hover:bg-paper hover:text-ink self-end"
            aria-label="Collapse sidebar"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>

          {/* Main Navigation */}
          <div className="flex-1 space-y-1">
            <NavItem to="/" icon={Home}>Home</NavItem>
            <NavItem to="/upload" icon={Upload}>Upload</NavItem>
            
            <SignedIn>
              <div className="pt-4">
                <p className="px-3 text-xs font-semibold text-ink/40 uppercase tracking-wider mb-2">
                  Workspace
                </p>
                <NavItem to="/dashboard" icon={BarChart3}>Dashboard</NavItem>
                <NavItem to="/enterprise-dashboard" icon={BarChart3}>Analytics</NavItem>
              </div>
              
              <div className="pt-4">
                <p className="px-3 text-xs font-semibold text-ink/40 uppercase tracking-wider mb-2">
                  Tools
                </p>
                <NavItem to="/viewer" icon={FileText}>File Viewer</NavItem>
                <NavItem to="/scale-calibration" icon={Ruler}>Scale Calibration</NavItem>
              </div>
              
              <div className="pt-4">
                <p className="px-3 text-xs font-semibold text-ink/40 uppercase tracking-wider mb-2">
                  Account
                </p>
                <NavItem to="/settings" icon={Settings}>Settings</NavItem>
                <NavItem to="/exports" icon={Download}>Exports</NavItem>
                <NavItem to="/help" icon={HelpCircle}>Help</NavItem>
                <NavItem to="/team" icon={Users}>Team</NavItem>
              </div>
            </SignedIn>
          </div>

          {/* Bottom Section */}
          <div className="border-t border-ink/10 pt-4 space-y-1">
            <SignedIn>
              <div className="flex items-center gap-2 px-3 py-2">
                <UserButton afterSignOutUrl="/" />
              </div>
            </SignedIn>
            
            <SignedOut>
              <NavLink
                to="/upload"
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium bg-ink text-paper hover:bg-ink/90 transition-colors"
              >
                <Upload className="h-4 w-4" />
                Analyze Blueprint
              </NavLink>
            </SignedOut>
          </div>
        </nav>
      </aside>

      {/* Overlay for mobile */}
      {collapsed && (
        <div 
          className="lg:hidden fixed inset-0 bg-ink/20 backdrop-blur-sm z-20"
          onClick={() => setCollapsed(true)}
        />
      )}
    </>
  )
}
