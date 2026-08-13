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
import SignIn from '@/pages/SignIn'
import SignUp from '@/pages/SignUp'
import EnterpriseAnalytics from '@/pages/EnterpriseAnalytics'
import NewAnalytics from '@/pages/NewAnalytics'
import NewDashboard from '@/pages/NewDashboard'
import FloorComparison from '@/pages/FloorComparison'
import PublicShare from '@/pages/PublicShare'
import PublicView from '@/pages/PublicView'
import CostBenchmarking from '@/pages/CostBenchmarking'
import ProjectDetail from '@/pages/ProjectDetail'
import Settings from '@/pages/Settings'
import Profile from '@/pages/Profile'
import ExportCenter from '@/pages/ExportCenter'
import Help from '@/pages/Help'
import TeamManagement from '@/pages/TeamManagement'
import Viewer from '@/pages/Viewer'
import ScaleCalibrationPage from '@/pages/ScaleCalibrationPage'
import CalibrationHistory from '@/pages/CalibrationHistory'

const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || ''

export default function App() {
  if (!clerkPubKey || clerkPubKey.includes('your_clerk')) {
    return (
      <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 24, fontFamily: 'system-ui' }}>
        <div style={{ maxWidth: 520 }}>
          <h1 style={{ fontSize: 22, marginBottom: 12 }}>Missing Clerk publishable key</h1>
          <p style={{ lineHeight: 1.5, marginBottom: 12 }}>
            Create <code>frontend/.env</code> with{' '}
            <code>VITE_CLERK_PUBLISHABLE_KEY=pk_test_...</code> (same value as{' '}
            <code>CLERK_PUBLISHABLE_KEY</code> in <code>backend/.env</code>), then restart{' '}
            <code>npm run dev</code>.
          </p>
        </div>
      </div>
    )
  }

  return (
    <ClerkProvider publishableKey={clerkPubKey}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<Home />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/results/:fileId?" element={<Results />} />
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
            <Route path="/new-dashboard" element={<NewDashboard />} />
            <Route path="/new-analytics" element={<NewAnalytics />} />
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
            <Route
              path="/settings"
              element={
                <SignedIn>
                  <Settings />
                </SignedIn>
              }
            />
            <Route
              path="/profile"
              element={
                <SignedIn>
                  <Profile />
                </SignedIn>
              }
            />
            <Route
              path="/exports"
              element={
                <SignedIn>
                  <ExportCenter />
                </SignedIn>
              }
            />
            <Route
              path="/help"
              element={
                <SignedIn>
                  <Help />
                </SignedIn>
              }
            />
            <Route
              path="/team"
              element={
                <SignedIn>
                  <TeamManagement />
                </SignedIn>
              }
            />
            <Route path="/viewer" element={<Viewer />} />
            <Route
              path="/scale-calibration"
              element={
                <SignedIn>
                  <ScaleCalibrationPage />
                </SignedIn>
              }
            />
            <Route
              path="/calibration-history"
              element={
                <SignedIn>
                  <CalibrationHistory />
                </SignedIn>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Route>
          {/* Public routes (no auth required) */}
          <Route path="/share/:token" element={<PublicView />} />
          <Route path="/sign-in" element={<SignIn />} />
          <Route path="/sign-up" element={<SignUp />} />
        </Routes>
      </BrowserRouter>
    </ClerkProvider>
  )
}
