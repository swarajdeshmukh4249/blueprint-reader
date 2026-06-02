import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { publicSharesApi, blueprintFilesApi } from '../lib/api'
import { ArrowLeft, Share2, Copy, Check, Shield, Calendar, Eye, Trash2, Power } from 'lucide-react'

interface PublicShare {
  id: string
  share_token: string
  blueprint_file_id: string
  project_id: string
  title: string | null
  description: string | null
  has_password: boolean
  expires_at: string | null
  view_count: number
  last_viewed_at: string | null
  is_active: boolean
  created_at: string
  share_url: string
}

interface BlueprintFile {
  id: string
  filename: string
  status: string
  total_area: number | null
  room_count: number | null
}

export default function PublicShare() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  
  const [shares, setShares] = useState<PublicShare[]>([])
  const [files, setFiles] = useState<BlueprintFile[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [copiedToken, setCopiedToken] = useState<string | null>(null)
  
  // Form state
  const [selectedFileId, setSelectedFileId] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [password, setPassword] = useState('')
  const [expiresInDays, setExpiresInDays] = useState<number | null>(null)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadShares()
    loadFiles()
  }, [projectId])

  const loadShares = async () => {
    try {
      const data: PublicShare[] = await publicSharesApi.list(projectId!)
      setShares(data)
    } catch (err) {
      console.error('Failed to load shares:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadFiles = async () => {
    try {
      const data: BlueprintFile[] = await blueprintFilesApi.list(projectId, 50)
      setFiles(data.filter(f => f.status === 'analyzed'))
    } catch (err) {
      console.error('Failed to load files:', err)
    }
  }

  const handleCreateShare = async () => {
    if (!selectedFileId) {
      setError('Please select a file to share')
      return
    }

    setCreating(true)
    setError(null)

    try {
      const share: PublicShare = await publicSharesApi.create({
        blueprint_file_id: selectedFileId,
        title: title || undefined,
        description: description || undefined,
        password: password || undefined,
        expires_in_days: expiresInDays || undefined,
      })
      
      setShares([share, ...shares])
      setShowCreateForm(false)
      setSelectedFileId('')
      setTitle('')
      setDescription('')
      setPassword('')
      setExpiresInDays(null)
      
      // Auto-copy the share URL
      const shareUrl = `${window.location.origin}/share/${share.share_token}`
      await navigator.clipboard.writeText(shareUrl)
      setCopiedToken(share.share_token)
      setTimeout(() => setCopiedToken(null), 2000)
    } catch (err: any) {
      setError(err.message || 'Failed to create share')
    } finally {
      setCreating(false)
    }
  }

  const handleCopyLink = async (token: string) => {
    const shareUrl = `${window.location.origin}/share/${token}`
    await navigator.clipboard.writeText(shareUrl)
    setCopiedToken(token)
    setTimeout(() => setCopiedToken(null), 2000)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this share?')) return
    
    try {
      await publicSharesApi.delete(id)
      setShares(shares.filter(s => s.id !== id))
    } catch (err) {
      console.error('Failed to delete share:', err)
    }
  }

  const handleDeactivate = async (id: string) => {
    try {
      await publicSharesApi.deactivate(id)
      setShares(shares.map(s => s.id === id ? { ...s, is_active: false } : s))
    } catch (err) {
      console.error('Failed to deactivate share:', err)
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleDateString()
  }

  const formatCurrency = (value: number | null) => {
    if (value === null) return '—'
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back
        </button>

        <div className="bg-white rounded-xl border p-8">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Client Share Portal</h1>
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Share2 className="w-4 h-4 mr-2" />
              {showCreateForm ? 'Cancel' : 'Create Share'}
            </button>
          </div>

          {showCreateForm && (
            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Create New Share Link</h2>
              
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select File *
                  </label>
                  <select
                    value={selectedFileId}
                    onChange={(e) => setSelectedFileId(e.target.value)}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="">Select a file...</option>
                    {files.map((file) => (
                      <option key={file.id} value={file.id}>
                        {file.filename} ({file.total_area || 0} sq ft, {file.room_count || 0} rooms)
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Title
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Project BOQ - Floor Plan"
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief description of this BOQ..."
                    rows={2}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Password (Optional)
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Leave empty for no password"
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Expires In (Days, Optional)
                  </label>
                  <input
                    type="number"
                    value={expiresInDays || ''}
                    onChange={(e) => setExpiresInDays(e.target.value ? parseInt(e.target.value) : null)}
                    placeholder="Leave empty for no expiration"
                    min="1"
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
              </div>

              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}

              <div className="mt-4 flex gap-3">
                <button
                  onClick={handleCreateShare}
                  disabled={creating || !selectedFileId}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
                >
                  {creating ? 'Creating...' : 'Create Share Link'}
                </button>
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {loading ? (
            <div className="text-center py-12 text-gray-500">Loading shares...</div>
          ) : shares.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Share2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="mb-4">No share links created yet</p>
              <p className="text-sm">Create a share link to share BOQ with clients</p>
            </div>
          ) : (
            <div className="space-y-4">
              {shares.map((share) => (
                <div key={share.id} className="border rounded-lg p-4 hover:shadow-md transition">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-gray-900">
                          {share.title || 'Untitled Share'}
                        </h3>
                        {!share.is_active && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                            Inactive
                          </span>
                        )}
                        {share.has_password && (
                          <span title="Password protected">
                            <Shield className="w-4 h-4 text-gray-400" />
                          </span>
                        )}
                      </div>
                      
                      {share.description && (
                        <p className="text-sm text-gray-600 mb-3">{share.description}</p>
                      )}
                      
                      <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                        <div className="flex items-center">
                          <Eye className="w-4 h-4 mr-1" />
                          {share.view_count} views
                        </div>
                        {share.last_viewed_at && (
                          <div className="flex items-center">
                            <Calendar className="w-4 h-4 mr-1" />
                            Last viewed: {formatDate(share.last_viewed_at)}
                          </div>
                        )}
                        {share.expires_at && (
                          <div className="flex items-center">
                            <Calendar className="w-4 h-4 mr-1" />
                            Expires: {formatDate(share.expires_at)}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => handleCopyLink(share.share_token)}
                        className="p-2 hover:bg-gray-100 rounded-lg"
                        title="Copy link"
                      >
                        {copiedToken === share.share_token ? (
                          <Check className="w-4 h-4 text-green-600" />
                        ) : (
                          <Copy className="w-4 h-4 text-gray-600" />
                        )}
                      </button>
                      
                      {share.is_active ? (
                        <button
                          onClick={() => handleDeactivate(share.id)}
                          className="p-2 hover:bg-gray-100 rounded-lg"
                          title="Deactivate"
                        >
                          <Power className="w-4 h-4 text-gray-600" />
                        </button>
                      ) : null}
                      
                      <button
                        onClick={() => handleDelete(share.id)}
                        className="p-2 hover:bg-red-50 rounded-lg"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
