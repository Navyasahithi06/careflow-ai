import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { Token, QueueStatus } from '../../types'

export default function UserToken() {
  const [tokens, setTokens] = useState<Token[]>([])
  const [activeToken, setActiveToken] = useState<Token | null>(null)
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const getAuthHeaders = () => {
    const token = localStorage.getItem('cf_token')
    return { Authorization: `Bearer ${token}` }
  }

  const fetchTokens = useCallback(async () => {
    try {
      const res = await axios.get('/api/tokens/my', { headers: getAuthHeaders() })
      const data: Token[] = res.data
      setTokens(data)

      const active = data.find(
        (t) => t.status === 'WAITING' || t.status === 'CALLED' || t.status === 'IN_CONSULTATION'
      )
      setActiveToken(active || null)
      setError('')
    } catch {
      setError('Failed to load tokens')
    }
  }, [])

  const fetchQueueStatus = useCallback(async (doctorId: number, queueDate: string) => {
    try {
      const res = await axios.get(`/api/queue/doctor/${doctorId}`, {
        headers: getAuthHeaders(),
        params: { queue_date: queueDate },
      })
      setQueueStatus(res.data)
    } catch {
      // silent
    }
  }, [])

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      await fetchTokens()
      setLoading(false)
    }
    load()
  }, [fetchTokens])

  useEffect(() => {
    if (!activeToken) return
    fetchQueueStatus(activeToken.doctor_id, activeToken.queue_date)

    const interval = setInterval(() => {
      fetchQueueStatus(activeToken.doctor_id, activeToken.queue_date)
    }, 12000)
    return () => clearInterval(interval)
  }, [activeToken, fetchQueueStatus])

  const statusColor = (status: string) => {
    switch (status) {
      case 'WAITING': return 'bg-amber-100 text-amber-800 border-amber-300'
      case 'CALLED': return 'bg-green-100 text-green-800 border-green-300'
      case 'IN_CONSULTATION': return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'COMPLETED': return 'bg-gray-100 text-gray-600 border-gray-300'
      case 'SKIPPED': return 'bg-red-100 text-red-800 border-red-300'
      case 'CANCELLED': return 'bg-gray-100 text-gray-500 border-gray-300'
      default: return 'bg-gray-100 text-gray-600 border-gray-300'
    }
  }

  const statusLabel = (status: string) => {
    switch (status) {
      case 'WAITING': return 'Waiting in Queue'
      case 'CALLED': return 'Called - Please Proceed'
      case 'IN_CONSULTATION': return 'In Consultation'
      case 'COMPLETED': return 'Completed'
      case 'SKIPPED': return 'Skipped'
      case 'CANCELLED': return 'Cancelled'
      default: return status
    }
  }

  const formatDateTime = (date: string, time: string) => {
    const d = new Date(date + 'T00:00:00')
    const dateStr = d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    const timeStr = time.slice(0, 5)
    return `${dateStr} at ${timeStr}`
  }

  const patientsAhead = queueStatus && activeToken
    ? Math.max(0, queueStatus.current_token !== null ? activeToken.token_number - queueStatus.current_token - 1 : activeToken.token_number - 1)
    : null

  const estimatedWait = queueStatus ? queueStatus.estimated_wait_minutes : null

  const currentServing = queueStatus?.current_token ?? null

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Queue Token</h1>
          <p className="text-gray-500 mt-1">Your current queue position and token status</p>
        </div>
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-gray-500">Loading your tokens...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Queue Token</h1>
          <p className="text-gray-500 mt-1">Your current queue position and token status</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-700 font-medium">{error}</p>
          <button
            onClick={async () => { setLoading(true); setError(''); await fetchTokens(); setLoading(false) }}
            className="mt-3 text-sm text-red-600 underline hover:text-red-800"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Queue Token</h1>
        <p className="text-gray-500 mt-1">Your current queue position and token status</p>
      </div>

      {tokens.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="text-5xl mb-4">🎫</div>
          <h3 className="text-lg font-semibold text-gray-900">No Tokens Yet</h3>
          <p className="text-gray-500 mt-1">Book an appointment to get your queue token.</p>
        </div>
      ) : (
        <>
          {activeToken ? (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-lg overflow-hidden">
              <div className="bg-indigo-600 px-6 py-4">
                <h2 className="text-center text-sm font-semibold text-indigo-100 uppercase tracking-wider">
                  Your Token
                </h2>
              </div>

              <div className="px-6 py-8 flex flex-col items-center">
                <p className="text-7xl font-extrabold text-gray-900 tracking-tight">
                  #{activeToken.token_number}
                </p>

                <div className="mt-6 text-center">
                  <p className="text-lg font-semibold text-gray-900">{activeToken.doctor_name}</p>
                  <p className="text-sm text-gray-500">{activeToken.doctor_specialization}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    {formatDateTime(activeToken.queue_date, activeToken.appointment_time)}
                  </p>
                </div>

                <div className="mt-6 w-full max-w-sm">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-gray-50 rounded-lg p-3 text-center border border-gray-200">
                      <p className="text-xs text-gray-500 font-medium">Serving</p>
                      <p className="text-xl font-bold text-gray-900 mt-1">
                        {currentServing !== null ? `#${currentServing}` : '--'}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3 text-center border border-gray-200">
                      <p className="text-xs text-gray-500 font-medium">Ahead</p>
                      <p className="text-xl font-bold text-gray-900 mt-1">
                        {patientsAhead !== null ? patientsAhead : '--'}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3 text-center border border-gray-200">
                      <p className="text-xs text-gray-500 font-medium">Wait</p>
                      <p className="text-xl font-bold text-gray-900 mt-1">
                        {estimatedWait !== null ? `${estimatedWait}m` : '--'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-6">
                  {activeToken.status === 'CALLED' ? (
                    <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold bg-green-100 text-green-800 border border-green-300 animate-pulse">
                      <span className="w-2 h-2 bg-green-500 rounded-full" />
                      {statusLabel(activeToken.status)}
                    </span>
                  ) : (
                    <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold border ${statusColor(activeToken.status)}`}>
                      {statusLabel(activeToken.status)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
              <p className="text-gray-500">No active tokens. All your appointments have been processed.</p>
            </div>
          )}

          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">All Tokens</h2>
            <div className="space-y-3">
              {tokens.map((token) => (
                <div
                  key={token.id}
                  className={`bg-white rounded-xl border p-4 flex items-center justify-between ${
                    activeToken && token.id === activeToken.id ? 'border-indigo-300 ring-1 ring-indigo-200' : 'border-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg bg-indigo-50 flex items-center justify-center">
                      <span className="text-lg font-bold text-indigo-700">#{token.token_number}</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{token.doctor_name}</p>
                      <p className="text-sm text-gray-500">
                        {token.doctor_specialization} &middot; {formatDateTime(token.queue_date, token.appointment_time)}
                      </p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${statusColor(token.status)}`}>
                    {token.status.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
