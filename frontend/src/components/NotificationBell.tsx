import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import type { AppNotification } from '../types'

function getAuthHeaders() {
  const token = localStorage.getItem('cf_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function relativeTime(dateStr: string) {
  if (!dateStr) return ''
  const then = new Date(dateStr).getTime()
  const diff = Date.now() - then
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

const typeIcon: Record<string, string> = {
  appointment_confirmed: '✅',
  payment_success: '💳',
  token_called: '🎫',
  consultation_completed: '💬',
  new_patient_registered: '👥',
}

export default function NotificationBell() {
  const { token } = useAuth()
  const [notifications, setNotifications] = useState<AppNotification[]>([])
  const [unread, setUnread] = useState(0)
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reconnecting, setReconnecting] = useState(false)

  const containerRef = useRef<HTMLDivElement>(null)
  const esRef = useRef<EventSource | null>(null)
  const retryRef = useRef<number | null>(null)
  const retryDelayRef = useRef(3)

  const fetchInbox = useCallback(async () => {
    try {
      const res = await axios.get<AppNotification[]>('/api/notifications', { headers: getAuthHeaders() })
      setNotifications(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load notifications')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchUnread = useCallback(async () => {
    try {
      const res = await axios.get<{ count: number }>('/api/notifications/unread-count', { headers: getAuthHeaders() })
      setUnread(res.data.count)
    } catch {
      setUnread(0)
    }
  }, [])

  useEffect(() => {
    if (!token) return
    setLoading(true)
    fetchInbox()
    fetchUnread()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  useEffect(() => {
    if (!token) return

    const connect = () => {
      const es = new EventSource(`/api/notifications/stream?token=${encodeURIComponent(token)}`)
      esRef.current = es

      es.onopen = () => {
        retryDelayRef.current = 3
        setReconnecting(false)
      }

      es.onmessage = (evt) => {
        if (evt.type !== 'notification') return
        try {
          const n = JSON.parse(evt.data) as AppNotification
          setNotifications((prev) => (prev.some((p) => p.id === n.id) ? prev : [n, ...prev].slice(0, 100)))
          if (!n.is_read) setUnread((u) => u + 1)
        } catch {
          // ignore malformed events
        }
      }

      es.onerror = () => {
        es.close()
        esRef.current = null
        setReconnecting(true)
        retryRef.current = window.setTimeout(() => connect(), retryDelayRef.current * 1000)
        retryDelayRef.current = Math.min(retryDelayRef.current * 2, 30)
      }
    }

    connect()

    return () => {
      if (esRef.current) esRef.current.close()
      if (retryRef.current) window.clearTimeout(retryRef.current)
      setReconnecting(false)
    }
  }, [token])

  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const handleMarkRead = async (n: AppNotification) => {
    if (n.is_read) return
    try {
      await axios.post(`/api/notifications/${n.id}/read`, {}, { headers: getAuthHeaders() })
      setNotifications((prev) => prev.map((p) => (p.id === n.id ? { ...p, is_read: true } : p)))
      setUnread((u) => Math.max(0, u - 1))
    } catch {
      // silent
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await axios.post('/api/notifications/read-all', {}, { headers: getAuthHeaders() })
      setNotifications((prev) => prev.map((p) => (p.is_read ? p : { ...p, is_read: true })))
      setUnread(0)
    } catch {
      // silent
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative p-2 text-gray-500 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors"
        title="Notifications"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unread > 0 && (
          <span className="absolute top-0.5 right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-[10px] font-semibold flex items-center justify-center">
            {unread > 99 ? '99+' : unread}
          </span>
        )}
        {reconnecting && (
          <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-amber-400 border-2 border-white" title="Reconnecting..."></span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl border border-gray-200 shadow-xl z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            {unread > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs font-medium text-primary-600 hover:text-primary-800"
              >
                Mark all as read
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-10 text-sm text-gray-400">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
                <span className="ml-2">Loading...</span>
              </div>
            ) : error ? (
              <div className="py-10 flex flex-col items-center text-sm text-gray-400">
                <span className="text-3xl mb-2">⚠️</span>
                <p>{error}</p>
              </div>
            ) : notifications.length === 0 ? (
              <div className="py-10 flex flex-col items-center text-sm text-gray-400">
                <span className="text-3xl mb-2">🔔</span>
                <p className="font-medium text-gray-500">No notifications yet</p>
                <p className="text-xs mt-1">Updates will appear here</p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {notifications.map((n) => (
                  <li key={n.id}>
                    <button
                      onClick={() => handleMarkRead(n)}
                      className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors flex items-start gap-3 ${
                        n.is_read ? 'bg-white' : 'bg-primary-50/40'
                      }`}
                    >
                      <span className="text-lg leading-none mt-0.5">{typeIcon[n.notification_type] || '🔔'}</span>
                      <span className="flex-1 min-w-0">
                        <span className="block text-sm font-medium text-gray-900">{n.title}</span>
                        <span className="block text-xs text-gray-600 mt-0.5">{n.message}</span>
                        <span className="block text-[11px] text-gray-400 mt-1">{relativeTime(n.created_at)}</span>
                      </span>
                      {!n.is_read && (
                        <span className="mt-1.5 w-2 h-2 rounded-full bg-primary-500 shrink-0"></span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}