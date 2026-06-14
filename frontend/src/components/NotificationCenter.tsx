import { useState, useEffect } from 'react'
import { Bell, Check, X, FileText, AlertCircle, CheckCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import { blueprintFilesApi, projectsApi } from '@/lib/api'

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  time: string
  read: boolean
}

export default function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadNotifications()
  }, [])

  const loadNotifications = async () => {
    try {
      const [filesData, projectsData] = await Promise.all([
        blueprintFilesApi.list(),
        projectsApi.list()
      ])

      // Convert blueprint files to notifications
      const fileNotifications: Notification[] = filesData.slice(0, 5).map(file => {
        const project = projectsData.find(p => p.id === file.project_id)
        return {
          id: file.id,
          type: file.status === 'analyzed' ? 'success' : file.status === 'failed' ? 'error' : 'info',
          title: file.status === 'analyzed' ? 'Analysis Complete' : file.status === 'failed' ? 'Analysis Failed' : 'Blueprint Uploaded',
          message: `${file.filename} for ${project?.name || 'Unknown Project'}`,
          time: new Date(file.created_at).toLocaleDateString(),
          read: true // Mark all as read by default
        }
      })

      setNotifications(fileNotifications)
    } catch (error) {
      console.error('Failed to load notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const unreadCount = notifications.filter(n => !n.read).length

  const markAsRead = (id: string) => {
    setNotifications(notifications.map(n => 
      n.id === id ? { ...n, read: true } : n
    ))
  }

  const markAllAsRead = () => {
    setNotifications(notifications.map(n => ({ ...n, read: true })))
  }

  const deleteNotification = (id: string) => {
    setNotifications(notifications.filter(n => n.id !== id))
  }

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />
      default:
        return <Info className="h-4 w-4 text-blue-500" />
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="group relative inline-flex h-9 w-9 items-center justify-center rounded-full border border-ink/15 bg-paper/60 text-ink/70 transition hover:bg-paper hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
        aria-label="Notifications"
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-accent text-[10px] font-medium text-paper">
            {unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-12 z-50 w-80 rounded-lg border border-ink/10 bg-paper shadow-xl">
            <div className="flex items-center justify-between border-b border-ink/10 p-4">
              <h3 className="font-display text-sm tracking-tight text-ink">Notifications</h3>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-xs text-accent hover:text-accent/80"
                >
                  Mark all as read
                </button>
              )}
            </div>

            <div className="max-h-96 overflow-y-auto">
              {loading ? (
                <div className="p-8 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-2 border-ink/10 border-t-accent mx-auto" />
                  <p className="mt-2 text-sm text-ink/50">Loading notifications...</p>
                </div>
              ) : notifications.length === 0 ? (
                <div className="p-8 text-center">
                  <Bell className="mx-auto h-8 w-8 text-ink/30" />
                  <p className="mt-2 text-sm text-ink/50">No notifications</p>
                </div>
              ) : (
                <div className="divide-y divide-ink/5">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={cn(
                        'relative p-4 transition-colors hover:bg-paper-2',
                        !notification.read && 'bg-accent/5'
                      )}
                    >
                      <div className="flex gap-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-paper">
                          {getIcon(notification.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <h4 className="text-sm font-medium text-ink">
                              {notification.title}
                            </h4>
                            {!notification.read && (
                              <button
                                onClick={() => markAsRead(notification.id)}
                                className="shrink-0 text-ink/50 hover:text-accent"
                              >
                                <Check className="h-3 w-3" />
                              </button>
                            )}
                          </div>
                          <p className="mt-1 text-xs text-ink/70 line-clamp-2">
                            {notification.message}
                          </p>
                          <p className="mt-1 text-xs text-ink/50">{notification.time}</p>
                        </div>
                        <button
                          onClick={() => deleteNotification(notification.id)}
                          className="shrink-0 text-ink/30 hover:text-ink/70"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="border-t border-ink/10 p-3">
              <button
                onClick={() => setIsOpen(false)}
                className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-2 text-sm text-ink transition hover:bg-paper-2"
              >
                View All Notifications
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
