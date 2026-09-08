import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'
import type { Token, QueueStatus, Doctor } from '../../types'

export default function AdminTokens() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [selectedDoctorId, setSelectedDoctorId] = useState<number | ''>('')
  const [queueDate, setQueueDate] = useState(new Date().toISOString().split('T')[0])
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [error, setError] = useState('')
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const headers = {
    Authorization: `Bearer ${localStorage.getItem('cf_token')}`,
  }

  const fetchDoctors = useCallback(async () => {
    try {
      const res = await axios.get<Doctor[]>('/api/admin/doctors', { headers })
      setDoctors(res.data)
    } catch {
      setError('Failed to load doctors.')
    }
  }, [])

  const fetchQueue = useCallback(async () => {
    if (!selectedDoctorId) return
    setLoading(true)
    setError('')
    try {
      const res = await axios.get<QueueStatus>('/api/admin/tokens/queue', {
        params: { doctor_id: selectedDoctorId, queue_date: queueDate },
        headers,
      })
      setQueueStatus(res.data)
    } catch {
      setError('Failed to load queue status.')
      setQueueStatus(null)
    } finally {
      setLoading(false)
    }
  }, [selectedDoctorId, queueDate])

  useEffect(() => {
    fetchDoctors()
  }, [fetchDoctors])

  useEffect(() => {
    if (selectedDoctorId && queueDate) {
      fetchQueue()
    }
  }, [selectedDoctorId, queueDate, fetchQueue])

  useEffect(() => {
    if (selectedDoctorId && queueDate) {
      intervalRef.current = setInterval(fetchQueue, 10_000)
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [selectedDoctorId, queueDate, fetchQueue])

  const performAction = async (action: string) => {
    if (!selectedDoctorId) return
    setActionLoading(action)
    setError('')
    try {
      await axios.post(
        `/api/admin/tokens/${action}`,
        { doctor_id: selectedDoctorId, queue_date: queueDate },
        { headers },
      )
      await fetchQueue()
    } catch {
      setError(`Failed to ${action.replace('-', ' ')}.`)
    } finally {
      setActionLoading(null)
    }
  }

  const hasCalledOrInConsult = queueStatus?.tokens.some(
    (t) => t.status === 'CALLED' || t.status === 'IN_CONSULTATION',
  )

  const hasWaiting = queueStatus?.tokens.some((t) => t.status === 'WAITING')
  const hasCalled = queueStatus?.tokens.some((t) => t.status === 'CALLED')
  const hasInConsultation = queueStatus?.tokens.some((t) => t.status === 'IN_CONSULTATION')

  const statusColor = (status: Token['status']) => {
    switch (status) {
      case 'WAITING':
        return 'bg-amber-100 text-amber-800'
      case 'CALLED':
        return 'bg-green-100 text-green-800 animate-pulse'
      case 'IN_CONSULTATION':
        return 'bg-blue-100 text-blue-800'
      case 'COMPLETED':
        return 'bg-gray-100 text-gray-800'
      case 'SKIPPED':
        return 'bg-red-100 text-red-800'
      case 'CANCELLED':
        return 'bg-gray-100 text-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Token Management</h1>
        <p className="text-gray-500 mt-1">Manage patient queue tokens</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Controls */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex flex-col">
            <label className="text-sm font-medium text-gray-700 mb-1">Doctor</label>
            <select
              value={selectedDoctorId}
              onChange={(e) => setSelectedDoctorId(e.target.value ? Number(e.target.value) : '')}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none"
            >
              <option value="">Select a doctor</option>
              {doctors.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.full_name} — {doc.specialization}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-sm font-medium text-gray-700 mb-1">Date</label>
            <input
              type="date"
              value={queueDate}
              onChange={(e) => setQueueDate(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none"
            />
          </div>

          <button
            onClick={fetchQueue}
            disabled={!selectedDoctorId || loading}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Loading…' : 'Load Queue'}
          </button>
        </div>
      </div>

      {/* Queue Summary */}
      {queueStatus && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Queue Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Doctor</span>
              <p className="font-medium text-gray-900">{queueStatus.doctor_name}</p>
            </div>
            <div>
              <span className="text-gray-500">Date</span>
              <p className="font-medium text-gray-900">{queueStatus.queue_date}</p>
            </div>
            <div>
              <span className="text-gray-500">Current Token</span>
              <p className="font-medium text-gray-900">{queueStatus.current_token ?? '—'}</p>
            </div>
            <div>
              <span className="text-gray-500">Called Token</span>
              <p className="font-medium text-gray-900">{queueStatus.currently_called ?? '—'}</p>
            </div>
            <div>
              <span className="text-gray-500">Total Waiting</span>
              <p className="font-medium text-gray-900">{queueStatus.total_waiting}</p>
            </div>
            <div>
              <span className="text-gray-500">Total Completed</span>
              <p className="font-medium text-gray-900">{queueStatus.total_completed}</p>
            </div>
            <div>
              <span className="text-gray-500">Total Skipped</span>
              <p className="font-medium text-gray-900">{queueStatus.total_skipped}</p>
            </div>
            <div>
              <span className="text-gray-500">Total Cancelled</span>
              <p className="font-medium text-gray-900">{queueStatus.total_cancelled}</p>
            </div>
            <div className="col-span-2 md:col-span-4">
              <span className="text-gray-500">Estimated Wait Time</span>
              <p className="font-medium text-gray-900">{queueStatus.estimated_wait_minutes} min</p>
            </div>
          </div>
        </div>
      )}

      {/* Queue Controls */}
      {queueStatus && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Queue Controls</h2>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => performAction('call-next')}
              disabled={hasCalledOrInConsult || !!actionLoading || !selectedDoctorId}
              className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {actionLoading === 'call-next' ? 'Calling…' : 'Call Next'}
            </button>

            <button
              onClick={() => performAction('start-consultation')}
              disabled={!hasCalled || !!actionLoading || !selectedDoctorId}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {actionLoading === 'start-consultation' ? 'Starting…' : 'Start Consultation'}
            </button>

            <button
              onClick={() => performAction('complete')}
              disabled={!hasInConsultation || !!actionLoading || !selectedDoctorId}
              className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {actionLoading === 'complete' ? 'Completing…' : 'Complete'}
            </button>

            <button
              onClick={() => performAction('skip')}
              disabled={(!hasWaiting && !hasCalled) || !!actionLoading || !selectedDoctorId}
              className="bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {actionLoading === 'skip' ? 'Skipping…' : 'Skip'}
            </button>

            <button
              onClick={() => performAction('recall')}
              disabled={!hasCalled || !!actionLoading || !selectedDoctorId}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {actionLoading === 'recall' ? 'Recalling…' : 'Recall'}
            </button>
          </div>
        </div>
      )}

      {/* Token List */}
      {queueStatus && queueStatus.tokens.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <h2 className="text-lg font-semibold text-gray-900 px-6 pt-6 pb-2">Token List</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Token #</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Patient Name</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Appointment Time</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-500">Status</th>
                </tr>
              </thead>
              <tbody>
                {queueStatus.tokens.map((token) => (
                  <tr key={token.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-6 py-3 font-medium text-gray-900">#{token.token_number}</td>
                    <td className="px-6 py-3 text-gray-700">{token.patient_name}</td>
                    <td className="px-6 py-3 text-gray-700">
                      {token.appointment_time ?? '—'}
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${statusColor(token.status)}`}
                      >
                        {token.status.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && selectedDoctorId && queueStatus && queueStatus.tokens.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <p className="text-gray-500 text-lg">No tokens in the queue for this doctor and date.</p>
        </div>
      )}

      {/* Loading Spinner */}
      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Pre-load prompt */}
      {!selectedDoctorId && !loading && (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <p className="text-gray-500 text-lg">Select a doctor and date to view the queue.</p>
        </div>
      )}
    </div>
  )
}
