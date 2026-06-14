import { useState } from 'react'
import { SignedIn, useUser } from '@clerk/clerk-react'
import { Bell, Globe, Lock, Palette, Shield, User } from 'lucide-react'
import Container from '@/components/Container'

export default function Settings() {
  const { user } = useUser()
  const [activeTab, setActiveTab] = useState('profile')

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'privacy', label: 'Privacy', icon: Lock },
    { id: 'language', label: 'Language', icon: Globe },
  ]

  return (
    <SignedIn>
      <div className="min-h-screen">
        <Container className="py-8">
          <div className="mb-8">
            <h1 className="font-display text-3xl tracking-tight text-ink">Settings</h1>
            <p className="mt-2 text-sm text-ink/70">
              Manage your account settings and preferences
            </p>
          </div>

          <div className="flex gap-8">
            {/* Sidebar */}
            <aside className="w-64 flex-shrink-0">
              <nav className="space-y-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                        activeTab === tab.id
                          ? 'bg-accent/10 text-accent'
                          : 'text-ink/70 hover:bg-paper-2 hover:text-ink'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {tab.label}
                    </button>
                  )
                })}
              </nav>
            </aside>

            {/* Content */}
            <main className="flex-1">
              {activeTab === 'profile' && <ProfileSettings user={user} />}
              {activeTab === 'notifications' && <NotificationSettings />}
              {activeTab === 'appearance' && <AppearanceSettings />}
              {activeTab === 'security' && <SecuritySettings />}
              {activeTab === 'privacy' && <PrivacySettings />}
              {activeTab === 'language' && <LanguageSettings />}
            </main>
          </div>
        </Container>
      </div>
    </SignedIn>
  )
}

function ProfileSettings({ user }: { user: any }) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-6">
        <h2 className="font-display text-xl tracking-tight text-ink">Profile Information</h2>
        <p className="mt-1 text-sm text-ink/70">
          Update your personal information and profile details
        </p>

        <form className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-ink">Full Name</label>
            <input
              type="text"
              defaultValue={user?.firstName && user?.lastName ? `${user.firstName} ${user.lastName}` : ''}
              className="mt-1 block w-full rounded-md border border-ink/15 bg-paper px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              placeholder="Enter your full name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink">Email Address</label>
            <input
              type="email"
              defaultValue={user?.emailAddresses[0]?.emailAddress || ''}
              className="mt-1 block w-full rounded-md border border-ink/15 bg-paper px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              placeholder="your@email.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink">Company</label>
            <input
              type="text"
              className="mt-1 block w-full rounded-md border border-ink/15 bg-paper px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              placeholder="Your company name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink">Job Title</label>
            <input
              type="text"
              className="mt-1 block w-full rounded-md border border-ink/15 bg-paper px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              placeholder="Your job title"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              className="rounded-full bg-ink px-6 py-2 text-sm font-medium text-paper transition hover:-translate-y-px hover:bg-ink/90"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function NotificationSettings() {
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [pushNotifications, setPushNotifications] = useState(false)
  const [analysisComplete, setAnalysisComplete] = useState(true)
  const [weeklyDigest, setWeeklyDigest] = useState(true)

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-6">
        <h2 className="font-display text-xl tracking-tight text-ink">Notification Preferences</h2>
        <p className="mt-1 text-sm text-ink/70">
          Choose how you want to be notified about updates and activities
        </p>

        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-ink">Email Notifications</h3>
              <p className="text-xs text-ink/70">Receive notifications via email</p>
            </div>
            <button
              onClick={() => setEmailNotifications(!emailNotifications)}
              className={`relative h-6 w-11 rounded-full transition-colors ${
                emailNotifications ? 'bg-accent' : 'bg-ink/20'
              }`}
            >
              <span
                className={`absolute top-1 h-4 w-4 rounded-full bg-paper transition-transform ${
                  emailNotifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-ink">Push Notifications</h3>
              <p className="text-xs text-ink/70">Receive browser push notifications</p>
            </div>
            <button
              onClick={() => setPushNotifications(!pushNotifications)}
              className={`relative h-6 w-11 rounded-full transition-colors ${
                pushNotifications ? 'bg-accent' : 'bg-ink/20'
              }`}
            >
              <span
                className={`absolute top-1 h-4 w-4 rounded-full bg-paper transition-transform ${
                  pushNotifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-ink">Analysis Complete</h3>
              <p className="text-xs text-ink/70">Notify when blueprint analysis is complete</p>
            </div>
            <button
              onClick={() => setAnalysisComplete(!analysisComplete)}
              className={`relative h-6 w-11 rounded-full transition-colors ${
                analysisComplete ? 'bg-accent' : 'bg-ink/20'
              }`}
            >
              <span
                className={`absolute top-1 h-4 w-4 rounded-full bg-paper transition-transform ${
                  analysisComplete ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-ink">Weekly Digest</h3>
              <p className="text-xs text-ink/70">Receive weekly summary of activities</p>
            </div>
            <button
              onClick={() => setWeeklyDigest(!weeklyDigest)}
              className={`relative h-6 w-11 rounded-full transition-colors ${
                weeklyDigest ? 'bg-accent' : 'bg-ink/20'
              }`}
            >
              <span
                className={`absolute top-1 h-4 w-4 rounded-full bg-paper transition-transform ${
                  weeklyDigest ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function AppearanceSettings() {
  const { isDark, toggleTheme } = useTheme()

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-6">
        <h2 className="font-display text-xl tracking-tight text-ink">Appearance</h2>
        <p className="mt-1 text-sm text-ink/70">
          Customize the look and feel of your experience
        </p>

        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-ink">Dark Mode</h3>
              <p className="text-xs text-ink/70">Switch between light and dark theme</p>
            </div>
            <button
              onClick={toggleTheme}
              className={`relative h-6 w-11 rounded-full transition-colors ${
                isDark ? 'bg-accent' : 'bg-ink/20'
              }`}
            >
              <span
                className={`absolute top-1 h-4 w-4 rounded-full bg-paper transition-transform ${
                  isDark ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink">Font Size</label>
            <select className="mt-1 block w-full rounded-md border border-ink/15 bg-paper px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent">
              <option>Small</option>
              <option selected>Medium</option>
              <option>Large</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  )
}

function SecuritySettings() {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-6">
        <h2 className="font-display text-xl tracking-tight text-ink">Security</h2>
        <p className="mt-1 text-sm text-ink/70">
          Manage your account security settings
        </p>

        <div className="mt-6 space-y-4">
          <button className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-left text-sm text-ink transition hover:bg-paper-2">
            <div className="font-medium">Change Password</div>
            <div className="text-xs text-ink/70">Update your account password</div>
          </button>

          <button className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-left text-sm text-ink transition hover:bg-paper-2">
            <div className="font-medium">Two-Factor Authentication</div>
            <div className="text-xs text-ink/70">Add an extra layer of security</div>
          </button>

          <button className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-left text-sm text-ink transition hover:bg-paper-2">
            <div className="font-medium">Active Sessions</div>
            <div className="text-xs text-ink/70">Manage your active login sessions</div>
          </button>
        </div>
      </div>
    </div>
  )
}

function PrivacySettings() {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-6">
        <h2 className="font-display text-xl tracking-tight text-ink">Privacy</h2>
        <p className="mt-1 text-sm text-ink/70">
          Control your privacy settings and data sharing preferences
        </p>

        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-ink">Profile Visibility</h3>
              <p className="text-xs text-ink/70">Make your profile visible to others</p>
            </div>
            <button className="relative h-6 w-11 rounded-full bg-ink/20 transition-colors">
              <span className="absolute top-1 h-4 w-4 translate-x-1 rounded-full bg-paper transition-transform" />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-ink">Analytics Sharing</h3>
              <p className="text-xs text-ink/70">Share anonymous usage data</p>
            </div>
            <button className="relative h-6 w-11 rounded-full bg-accent transition-colors">
              <span className="absolute top-1 h-4 w-4 translate-x-6 rounded-full bg-paper transition-transform" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function LanguageSettings() {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-6">
        <h2 className="font-display text-xl tracking-tight text-ink">Language & Region</h2>
        <p className="mt-1 text-sm text-ink/70">
          Set your language and regional preferences
        </p>

        <div className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-ink">Language</label>
            <select className="mt-1 block w-full rounded-md border border-ink/15 bg-paper px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent">
              <option selected>English (US)</option>
              <option>English (UK)</option>
              <option>Spanish</option>
              <option>French</option>
              <option>German</option>
              <option>Hindi</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink">Timezone</label>
            <select className="mt-1 block w-full rounded-md border border-ink/15 bg-paper px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent">
              <option selected>UTC</option>
              <option>EST</option>
              <option>PST</option>
              <option>IST</option>
              <option>CET</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  )
}

// Import useTheme hook
function useTheme() {
  const [isDark, setIsDark] = useState(false)
  
  const toggleTheme = () => {
    setIsDark(!isDark)
    document.documentElement.classList.toggle('dark')
  }
  
  return { isDark, toggleTheme }
}
