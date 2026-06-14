import { SignedIn, useUser } from '@clerk/clerk-react'
import { Calendar, Clock, FileText, MapPin, User } from 'lucide-react'
import Container from '@/components/Container'
import { useState, useEffect } from 'react'
import { projectsApi, blueprintFilesApi } from '@/lib/api'

export default function Profile() {
  const { user } = useUser()
  const [projects, setProjects] = useState<any[]>([])
  const [blueprintFiles, setBlueprintFiles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [projectsData, filesData] = await Promise.all([
        projectsApi.list(),
        blueprintFilesApi.list()
      ])
      setProjects(projectsData)
      setBlueprintFiles(filesData)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const recentActivity = blueprintFiles.slice(0, 4).map(file => {
    const project = projects.find(p => p.id === file.project_id)
    return {
      title: `${file.status === 'analyzed' ? 'Analyzed' : 'Uploaded'} blueprint for ${project?.name || 'Unknown Project'}`,
      time: new Date(file.created_at).toLocaleDateString(),
      icon: <FileText className="h-4 w-4" />
    }
  })

  return (
    <SignedIn>
      <div className="min-h-screen">
        <Container className="py-8">
          <div className="mb-8">
            <h1 className="font-display text-3xl tracking-tight text-ink">Profile</h1>
            <p className="mt-2 text-sm text-ink/70">
              View and manage your profile information
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Profile Card */}
            <div className="lg:col-span-1">
              <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-6">
                <div className="flex flex-col items-center text-center">
                  <div className="h-24 w-24 rounded-full bg-accent/10 flex items-center justify-center">
                    <User className="h-12 w-12 text-accent" />
                  </div>
                  <h2 className="mt-4 font-display text-xl tracking-tight text-ink">
                    {user?.firstName && user?.lastName ? `${user.firstName} ${user.lastName}` : user?.emailAddresses[0]?.emailAddress || 'User'}
                  </h2>
                  <p className="text-sm text-ink/70">{user?.emailAddresses[0]?.emailAddress || ''}</p>
                  
                  <div className="mt-4 flex gap-2">
                    <button className="rounded-full bg-ink px-4 py-2 text-sm font-medium text-paper transition hover:-translate-y-px hover:bg-ink/90">
                      Edit Profile
                    </button>
                  </div>
                </div>

                <div className="mt-6 space-y-3 border-t border-ink/10 pt-6">
                  <div className="flex items-center gap-3 text-sm">
                    <Calendar className="h-4 w-4 text-ink/50" />
                    <span className="text-ink/70">
                      Joined {user?.createdAt ? new Date(user.createdAt).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : 'Recently'}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <Clock className="h-4 w-4 text-ink/50" />
                    <span className="text-ink/70">Last active Today</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Activity & Stats */}
            <div className="lg:col-span-2 space-y-6">
              {/* Stats */}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-4">
                  <div className="text-2xl font-display text-ink">{loading ? '-' : projects.length}</div>
                  <div className="text-xs text-ink/70">Projects</div>
                </div>
                <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-4">
                  <div className="text-2xl font-display text-ink">{loading ? '-' : blueprintFiles.filter(f => f.status === 'analyzed').length}</div>
                  <div className="text-xs text-ink/70">Blueprints Analyzed</div>
                </div>
                <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-4">
                  <div className="text-2xl font-display text-ink">{loading ? '-' : blueprintFiles.filter(f => f.status === 'analyzed').length}</div>
                  <div className="text-xs text-ink/70">BOQs Generated</div>
                </div>
                <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-4">
                  <div className="text-2xl font-display text-ink">{loading ? '-' : projects.filter(p => p.status === 'active').length}</div>
                  <div className="text-xs text-ink/70">Active Projects</div>
                </div>
              </div>

              {/* Recent Activity */}
              <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-6">
                <h3 className="font-display text-lg tracking-tight text-ink">Recent Activity</h3>
                <p className="mt-1 text-sm text-ink/70">Your latest actions and updates</p>

                {loading ? (
                  <div className="mt-4 text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-2 border-ink/10 border-t-accent mx-auto" />
                    <p className="mt-4 text-sm text-ink/70">Loading activity...</p>
                  </div>
                ) : recentActivity.length > 0 ? (
                  <div className="mt-4 space-y-4">
                    {recentActivity.map((activity, index) => (
                      <ActivityItem
                        key={index}
                        title={activity.title}
                        time={activity.time}
                        icon={activity.icon}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="mt-4 text-center py-8 text-sm text-ink/70">
                    No recent activity
                  </div>
                )}
              </div>

              {/* Skills & Expertise */}
              <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-6">
                <h3 className="font-display text-lg tracking-tight text-ink">Skills & Expertise</h3>
                <p className="mt-1 text-sm text-ink/70">Your professional expertise areas</p>

                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="rounded-full border border-ink/15 bg-paper px-3 py-1 text-xs text-ink">
                    Architectural Design
                  </span>
                  <span className="rounded-full border border-ink/15 bg-paper px-3 py-1 text-xs text-ink">
                    Construction Management
                  </span>
                  <span className="rounded-full border border-ink/15 bg-paper px-3 py-1 text-xs text-ink">
                    Cost Estimation
                  </span>
                  <span className="rounded-full border border-ink/15 bg-paper px-3 py-1 text-xs text-ink">
                    Blueprint Analysis
                  </span>
                  <span className="rounded-full border border-ink/15 bg-paper px-3 py-1 text-xs text-ink">
                    Project Planning
                  </span>
                </div>
              </div>
            </div>
          </div>
        </Container>
      </div>
    </SignedIn>
  )
}

function ActivityItem({ title, time, icon }: { title: string; time: string; icon: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-ink/5 bg-paper p-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/10 text-accent">
        {icon}
      </div>
      <div className="flex-1">
        <div className="text-sm text-ink">{title}</div>
        <div className="text-xs text-ink/50">{time}</div>
      </div>
    </div>
  )
}
