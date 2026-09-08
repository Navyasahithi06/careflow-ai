import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import type { HistoryTimelineEntry } from '../../types'
import AttachmentSection from '../../components/AttachmentSection'

function getAuthHeaders() {
  const token = localStorage.getItem('cf_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const typeBadge: Record<string, { label: string; className: string }> = {
  DIAGNOSIS: { label: 'Diagnosis', className: 'bg-blue-100 text-blue-800' },
  PRESCRIPTION: { label: 'Prescription', className: 'bg-green-100 text-green-800' },
  LAB_REPORT: { label: 'Lab Report', className: 'bg-purple-100 text-purple-800' },
  GENERAL: { label: 'General', className: 'bg-gray-100 text-gray-700' },
  CONSULTATION: { label: 'Consultation', className: 'bg-amber-100 text-amber-800' },
}

export default function UserHistory() {
  const [timeline, setTimeline] = useState<HistoryTimelineEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('')

  const fetchHistory = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await axios.get('/api/user/history', { headers: getAuthHeaders() })
      setTimeline(res.data.timeline || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch history')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory])

  const filtered = filter ? timeline.filter((e) => e.type === filter) : timeline

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Medical History</h1>
        <p className="text-gray-500 mt-1">Your complete medical records and consultations</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
          <button onClick={fetchHistory} className="ml-3 underline font-medium hover:text-red-900">Retry</button>
        </div>
      )}

      <div className="flex gap-2">
        {[
          { value: '', label: 'All' },
          { value: 'medical_record', label: 'Medical Records' },
          { value: 'consultation', label: 'Consultations' },
        ].map((opt) => (
          <button
            key={opt.value}
            onClick={() => setFilter(opt.value)}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              filter === opt.value
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-gray-500 text-sm">Loading your history...</span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 py-20 flex flex-col items-center justify-center text-gray-400">
          <span className="text-5xl mb-4">📋</span>
          <p className="text-lg font-medium text-gray-500">No records yet</p>
          <p className="text-sm mt-1">Your medical records and consultations will appear here</p>
        </div>
      ) : (
        <div className="relative">
          <div className="absolute left-4 top-0 bottom-0 w-px bg-gray-200"></div>
          <div className="space-y-4">
            {filtered.map((entry) => {
              const badge = typeBadge[entry.record_type] || typeBadge.GENERAL
              return (
                <div key={`${entry.type}-${entry.id}`} className="relative pl-12">
                  <div
                    className={`absolute left-0 top-2 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm ${
                      entry.type === 'consultation' ? 'bg-amber-500' : 'bg-primary-600'
                    }`}
                  >
                    {entry.type === 'consultation' ? '💬' : '📄'}
                  </div>
                  <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                    <div className="flex items-start justify-between gap-4 flex-wrap">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-gray-900">{entry.title}</span>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${badge.className}`}>
                            {badge.label}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{formatDate(entry.created_at)}</p>
                        {entry.doctor_name && (
                          <p className="text-xs text-gray-500 mt-1">
                            Doctor: <span className="font-medium text-gray-700">{entry.doctor_name}</span>
                          </p>
                        )}
                      </div>
                    </div>
                    {entry.diagnosis && (
                      <div className="mt-3">
                        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Diagnosis</p>
                        <p className="text-sm text-gray-800 mt-0.5">{entry.diagnosis}</p>
                      </div>
                    )}
                    {entry.prescriptions && (
                      <div className="mt-3">
                        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Prescriptions</p>
                        <p className="text-sm text-gray-800 mt-0.5 whitespace-pre-line">{entry.prescriptions}</p>
                      </div>
                    )}
                    {entry.notes && (
                      <div className="mt-3">
                        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Notes</p>
                        <p className="text-sm text-gray-800 mt-0.5">{entry.notes}</p>
                      </div>
                    )}
                    <AttachmentSection entityType={entry.type} entityId={entry.id} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
