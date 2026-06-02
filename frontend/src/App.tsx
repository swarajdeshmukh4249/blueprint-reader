import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ClerkProvider, SignedIn, SignedOut } from '@clerk/clerk-react'
import AppShell from '@/components/AppShell'
import About from '@/pages/About'
import Contact from '@/pages/Contact'
import Home from '@/pages/Home'
import NotFound from '@/pages/NotFound'
import Results from '@/pages/Results'
import Upload from '@/pages/Upload'
import Dashboard from '@/pages/Dashboard'
import EnterpriseAnalytics from '@/pages/EnterpriseAnalytics'
import FloorComparison from '@/pages/FloorComparison'
import PublicShare from '@/pages/PublicShare'
import PublicView from '@/pages/PublicView'
import CostBenchmarking from '@/pages/CostBenchmarking'
import ProjectDetail from '@/pages/ProjectDetail'

const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || ''

export default function App() {
  return (
    <ClerkProvider publishableKey={clerkPubKey}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<Home />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/results" element={<Results />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route 
              path="/dashboard" 
              element={
                <SignedIn>
                  <Dashboard />
                </SignedIn>
              } 
            />
            <Route
              path="/enterprise-dashboard"
              element={
                <SignedIn>
                  <EnterpriseAnalytics />
                </SignedIn>
              }
            />
            <Route
              path="/floor-comparison/:projectId"
              element={
                <SignedIn>
                  <FloorComparison />
                </SignedIn>
              }
            />
            <Route
              path="/public-share/:projectId"
              element={
                <SignedIn>
                  <PublicShare />
                </SignedIn>
              }
            />
            <Route
              path="/cost-benchmarking/:projectId"
              element={
                <SignedIn>
                  <CostBenchmarking />
                </SignedIn>
              }
            />
            <Route
              path="/project/:projectId"
              element={
                <SignedIn>
                  <ProjectDetail />
                </SignedIn>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Route>
          {/* Public routes (no auth required) */}
          <Route path="/share/:token" element={<PublicView />} />
        </Routes>
      </BrowserRouter>
    </ClerkProvider>
  )
}
