import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { publicSharesApi } from '../lib/api'
import { Lock, AlertCircle, FileText, Home, Eye } from 'lucide-react'

interface PublicShareView {
  title: string | null
  description: string | null
  filename: string
  analysis_result: any
  total_area: number | null
  room_count: number | null
  boq_total: number | null
  viewed_at: string
}

export default function PublicView() {
  const { token } = useParams()
  const navigate = useNavigate()
  
  const [data, setData] = useState<PublicShareView | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [password, setPassword] = useState('')
  const [passwordRequired, setPasswordRequired] = useState(false)

  useEffect(() => {
    loadData()
  }, [token])

  const loadData = async () => {
    setLoading(true)
    setError(null)

    try {
      const result: PublicShareView = await publicSharesApi.viewPublic(token!, password || undefined)
      setData(result)
    } catch (err: any) {
      if (err.message?.includes('password') || err.status === 401) {
        setPasswordRequired(true)
        setError('Password required to view this share')
      } else {
        setError(err.message || 'Failed to load shared content')
      }
    } finally {
      setLoading(false)
    }
  }

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    loadData()
  }

  const formatCurrency = (value: number | null) => {
    if (value === null) return '—'
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (error && passwordRequired) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="bg-white rounded-xl border p-8 max-w-md w-full">
          <div className="text-center mb-6">
            <Lock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Password Required</h2>
            <p className="text-gray-600">This share is password protected</p>
          </div>

          <form onSubmit={handlePasswordSubmit}>
            <div className="mb-4">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full border rounded-lg px-4 py-3"
                autoFocus
              />
            </div>
            <button
              type="submit"
              className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              View Share
            </button>
          </form>

          <button
            onClick={() => navigate('/')}
            className="w-full mt-4 px-4 py-2 border rounded-lg hover:bg-gray-50 text-sm"
          >
            Back to Home
          </button>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="bg-white rounded-xl border p-8 max-w-md w-full text-center">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Unable to Load Share</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Home
          </button>
        </div>
      </div>
    )
  }

  if (!data) {
    return null
  }

  const boq = data.analysis_result?.boq || []
  const rooms = data.analysis_result?.rooms || []

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-8 py-4 flex items-center justify-between">
          <div className="flex items-center">
            <FileText className="w-6 h-6 text-blue-600 mr-2" />
            <h1 className="text-xl font-semibold text-gray-900">
              {data.title || 'Shared BOQ'}
            </h1>
          </div>
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900 text-sm"
          >
            <Home className="w-4 h-4 inline mr-1" />
            Home
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-8 py-8">
        {/* Description */}
        {data.description && (
          <div className="bg-white rounded-xl border p-6 mb-6">
            <p className="text-gray-600">{data.description}</p>
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-4 mb-6">
          <div className="bg-white rounded-xl border p-6">
            <div className="text-sm text-gray-600 mb-1">File</div>
            <div className="font-semibold text-gray-900 truncate">{data.filename}</div>
          </div>
          <div className="bg-white rounded-xl border p-6">
            <div className="text-sm text-gray-600 mb-1">Total Area</div>
            <div className="text-xl font-semibold text-gray-900">
              {data.total_area ? `${data.total_area} sq ft` : '—'}
            </div>
          </div>
          <div className="bg-white rounded-xl border p-6">
            <div className="text-sm text-gray-600 mb-1">Rooms</div>
            <div className="text-xl font-semibold text-gray-900">
              {data.room_count || rooms.length}
            </div>
          </div>
          <div className="bg-white rounded-xl border p-6">
            <div className="text-sm text-gray-600 mb-1">BOQ Total</div>
            <div className="text-xl font-semibold text-green-600">
              {formatCurrency(data.boq_total)}
            </div>
          </div>
        </div>

        {/* Rooms */}
        {rooms.length > 0 && (
          <div className="bg-white rounded-xl border mb-6">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Rooms</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Type
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Width
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Height
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Area
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {rooms.map((room: any, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">
                        {room.name || `Room ${idx + 1}`}
                      </td>
                      <td className="px-6 py-4 text-gray-600">
                        {room.room_type || '—'}
                      </td>
                      <td className="px-6 py-4 text-right text-gray-600">
                        {room.width ? `${room.width}'` : '—'}
                      </td>
                      <td className="px-6 py-4 text-right text-gray-600">
                        {room.height ? `${room.height}'` : '—'}
                      </td>
                      <td className="px-6 py-4 text-right text-gray-600">
                        {room.area ? `${room.area} sq ft` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* BOQ */}
        {boq.length > 0 && (
          <div className="bg-white rounded-xl border">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Bill of Quantities</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Item
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Unit
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Amount
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {boq.map((item: any, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">
                        {item.item || `Item ${idx + 1}`}
                      </td>
                      <td className="px-6 py-4 text-right text-gray-600">
                        {item.quantity || '—'}
                      </td>
                      <td className="px-6 py-4 text-right text-gray-600">
                        {item.unit || ''}
                      </td>
                      <td className="px-6 py-4 text-right text-gray-600">
                        {formatCurrency(item.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-50">
                  <tr>
                    <td colSpan={3} className="px-6 py-3 text-sm font-medium text-gray-900 text-right">
                      Total:
                    </td>
                    <td className="px-6 py-3 text-sm font-medium text-gray-900 text-right">
                      {formatCurrency(data.boq_total)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <div className="flex items-center justify-center mb-2">
            <Eye className="w-4 h-4 mr-1" />
            Viewed on {new Date(data.viewed_at).toLocaleString()}
          </div>
          <p>Shared via ArchVision</p>
        </div>
      </div>
    </div>
  )
}
