import { SignedIn, useUser } from '@clerk/clerk-react'
import { Users, UserPlus, Mail, Shield, MoreVertical, Crown, Search, Filter } from 'lucide-react'
import Container from '@/components/Container'
import { useState, useEffect } from 'react'
import { organizationsApi } from '@/lib/api'

interface TeamMember {
  id: string
  name: string
  email: string
  role: 'owner' | 'admin' | 'member' | 'viewer'
  status: 'active' | 'pending' | 'inactive'
  joinedAt: string
  avatar?: string
}

export default function TeamManagement() {
  const { user } = useUser()
  const [searchQuery, setSearchQuery] = useState('')
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<'admin' | 'member' | 'viewer'>('member')
  const [organizations, setOrganizations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const orgsData = await organizationsApi.list()
      setOrganizations(orgsData)
    } catch (error) {
      console.error('Failed to load organizations:', error)
    } finally {
      setLoading(false)
    }
  }

  // Create team members from organizations and current user
  const teamMembers: TeamMember[] = [
    {
      id: user?.id || 'current-user',
      name: user?.firstName && user?.lastName ? `${user.firstName} ${user.lastName}` : user?.emailAddresses[0]?.emailAddress || 'User',
      email: user?.emailAddresses[0]?.emailAddress || '',
      role: 'owner',
      status: 'active',
      joinedAt: user?.createdAt ? new Date(user.createdAt).toISOString().split('T')[0] : new Date().toISOString().split('T')[0]
    },
    ...organizations.map((org, index) => ({
      id: org.id,
      name: org.name,
      email: `${org.slug}@example.com`,
      role: 'member' as const,
      status: 'active' as const,
      joinedAt: new Date().toISOString().split('T')[0]
    }))
  ]

  const filteredMembers = teamMembers.filter(member =>
    member.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    member.email.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getRoleBadge = (role: TeamMember['role']) => {
    switch (role) {
      case 'owner':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-800">
            <Crown className="h-3 w-3" />
            Owner
          </span>
        )
      case 'admin':
        return (
          <span className="rounded-full bg-purple-100 px-2 py-1 text-xs font-medium text-purple-800">
            Admin
          </span>
        )
      case 'member':
        return (
          <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800">
            Member
          </span>
        )
      case 'viewer':
        return (
          <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-800">
            Viewer
          </span>
        )
    }
  }

  const getStatusBadge = (status: TeamMember['status']) => {
    switch (status) {
      case 'active':
        return (
          <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
            Active
          </span>
        )
      case 'pending':
        return (
          <span className="rounded-full bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-800">
            Pending
          </span>
        )
      case 'inactive':
        return (
          <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-800">
            Inactive
          </span>
        )
    }
  }

  const handleInvite = () => {
    console.log('Invite member:', { email: inviteEmail, role: inviteRole })
    setShowInviteModal(false)
    setInviteEmail('')
    setInviteRole('member')
  }

  return (
    <SignedIn>
      <div className="min-h-screen">
        <Container className="py-8">
          <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="font-display text-3xl tracking-tight text-ink">Team Management</h1>
              <p className="mt-2 text-sm text-ink/70">
                Manage team members and their permissions
              </p>
            </div>
            <button
              onClick={() => setShowInviteModal(true)}
              className="inline-flex items-center gap-2 rounded-full bg-ink px-6 py-3 text-sm font-medium text-paper transition hover:bg-ink/90"
            >
              <UserPlus className="h-4 w-4" />
              Invite Member
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-4">
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-ink/50" />
                <div>
                  <div className="text-2xl font-display text-ink">{loading ? '-' : teamMembers.length}</div>
                  <div className="text-xs text-ink/70">Total Members</div>
                </div>
              </div>
            </div>
            <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-4">
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-ink/50" />
                <div>
                  <div className="text-2xl font-display text-ink">
                    {loading ? '-' : teamMembers.filter(m => m.status === 'active').length}
                  </div>
                  <div className="text-xs text-ink/70">Active Members</div>
                </div>
              </div>
            </div>
            <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-4">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-ink/50" />
                <div>
                  <div className="text-2xl font-display text-ink">
                    {loading ? '-' : teamMembers.filter(m => m.status === 'pending').length}
                  </div>
                  <div className="text-xs text-ink/70">Pending Invites</div>
                </div>
              </div>
            </div>
          </div>

          {/* Search and Filter */}
          <div className="mb-6 flex gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink/50" />
              <input
                type="text"
                placeholder="Search members..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-ink/15 bg-paper pl-10 pr-4 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
            </div>
            <button className="flex items-center gap-2 rounded-lg border border-ink/15 bg-paper px-4 py-2 text-sm text-ink transition hover:bg-paper-2">
              <Filter className="h-4 w-4" />
              Filter
            </button>
          </div>

          {/* Team Members List */}
          <div className="rounded-lg border border-ink/10 bg-paper-2/50 overflow-hidden">
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-ink/10 border-t-accent mx-auto" />
                <p className="mt-4 text-sm text-ink/70">Loading team members...</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-paper">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-ink/70 uppercase tracking-wider">
                        Member
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-ink/70 uppercase tracking-wider">
                        Role
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-ink/70 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-ink/70 uppercase tracking-wider">
                        Joined
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-ink/70 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink/5">
                    {filteredMembers.map((member) => (
                    <tr key={member.id} className="hover:bg-paper/50">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-accent/10 flex items-center justify-center text-accent font-medium">
                            {member.name.charAt(0)}
                          </div>
                          <div>
                            <div className="text-sm font-medium text-ink">{member.name}</div>
                            <div className="text-xs text-ink/50">{member.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {getRoleBadge(member.role)}
                      </td>
                      <td className="px-6 py-4">
                        {getStatusBadge(member.status)}
                      </td>
                      <td className="px-6 py-4 text-sm text-ink/70">
                        {new Date(member.joinedAt).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button className="text-ink/50 hover:text-ink">
                          <MoreVertical className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            )}
          </div>

          {/* Invite Modal */}
          {showInviteModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-paper/80 backdrop-blur-sm">
              <div className="w-full max-w-md rounded-lg border border-ink/10 bg-paper p-6 shadow-xl">
                <h2 className="font-display text-xl tracking-tight text-ink mb-4">
                  Invite Team Member
                </h2>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-ink mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      placeholder="colleague@example.com"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-ink mb-1">
                      Role
                    </label>
                    <select
                      value={inviteRole}
                      onChange={(e) => setInviteRole(e.target.value as any)}
                      className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="member">Member - Can view and edit</option>
                      <option value="admin">Admin - Full access</option>
                      <option value="viewer">Viewer - Read only</option>
                    </select>
                  </div>
                </div>

                <div className="mt-6 flex gap-3">
                  <button
                    onClick={() => setShowInviteModal(false)}
                    className="flex-1 rounded-lg border border-ink/15 bg-paper px-4 py-2 text-sm text-ink transition hover:bg-paper-2"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleInvite}
                    className="flex-1 rounded-lg bg-ink px-4 py-2 text-sm font-medium text-paper transition hover:bg-ink/90"
                  >
                    Send Invite
                  </button>
                </div>
              </div>
            </div>
          )}
        </Container>
      </div>
    </SignedIn>
  )
}
