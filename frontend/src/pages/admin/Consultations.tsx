import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import type { ConsultationListItem, ConsultationNote } from '../../types'
import AttachmentSection from '../../components/AttachmentSection'

const API_BASE = '/api/admin/consultations'

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

function formatTime(timeStr: string) {
  if (!timeStr) return ''
  const [h, m] = timeStr.split(':')
  const hour = parseInt(h, 10)
  const suffix = hour >= 12 ? 'PM' : 'AM'
  const display = hour % 12 || 12
  return `${display}:${m} ${suffix}`
}

export default function Consultations() {
  const [items, setItems] = useState<ConsultationListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const [selectedAppt, setSelectedAppt] = useState<ConsultationListItem | null>(null)
  const [note, setNote] = useState<ConsultationNote | null>(null)
  const [showNoteModal, setShowNoteModal] = useState(false)
  const [noteForm, setNoteForm] = useState({ notes: '', diagnosis: '', prescriptions: '' })
  const [submitting, setSubmitting] = useState(false)
  const [noteError, setNoteError] = useState('')

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null)

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }, [])

  const fetchItems = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params: Record<string, string> = {}
      if (search) params.search = search
      if (statusFilter) params.status = statusFilter
      const res = await axios.get(`${API_BASE}/appointments`, { params, headers: getAuthHeaders() })
      setItems(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch consultations')
    } finally {
      setLoading(false)
    }
  }, [search, statusFilter])

  useEffect(() => {
    fetchItems()
  }, [fetchItems])

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchItems()
    }, 300)
    return () => clearTimeout(timer)
  }, [search, statusFilter])

  const openNoteModal = async (item: ConsultationListItem) => {
    setSelectedAppt(item)
    setNoteError('')
    if (item.note_id) {
      try {
        const res = await axios.get<ConsultationNote>(`${API_BASE}/notes/${item.note_id}`, { headers: getAuthHeaders() })
        setNote(res.data)
        setNoteForm({
          notes: res.data.notes || '',
          diagnosis: res.data.diagnosis || '',
          prescriptions: res.data.prescriptions || '',
        })
      } catch {
        setNote(null)
        setNoteForm({ notes: '', diagnosis: '', prescriptions: '' })
      }
    } else {
      setNote(null)
      setNoteForm({ notes: '', diagnosis: '', prescriptions: '' })
    }
    setShowNoteModal(true)
  }

  const closeModal = () => {
    setShowNoteModal(false)
    setSelectedAppt(null)
    setNote(null)
    setNoteForm({ notes: '', diagnosis: '', prescriptions: '' })
    setNoteError('')
  }

  const handleSaveNote = async () => {
    if (!selectedAppt) return
    setSubmitting(true)
    setNoteError('')
    try {
      if (note) {
        await axios.put(`${API_BASE}/notes/${note.id}`, noteForm, { headers: getAuthHeaders() })
        showToast('Consultation note updated successfully')
      } else {
        await axios.post(`${API_BASE}/appointments/${selectedAppt.appointment_id}/notes`, noteForm, { headers: getAuthHeaders() })
        showToast('Consultation note added successfully')
      }
      closeModal()
      fetchItems()
    } catch (err: any) {
      setNoteError(err.response?.data?.detail || 'Failed to save note')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white text-sm transition-all ${
            toast.type === 'success'
              ? 'bg-green-600'
              : toast.type === 'error'
              ? 'bg-red-600'
              : 'bg-blue-600'
          }`}
        >
          {toast.message}
        </div>
      )}

      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Consultations</h1>
          <p className="text-sm text-gray-500 mt-1">Manage doctor-patient consultations and notes</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
          <div className="p-4 flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search by patient name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div className="w-full sm:w-48">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">All Status</option>
                <option value="CONFIRMED">Confirmed</option>
                <option value="COMPLETED">Completed</option>
              </select>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">
            {error}
            <button onClick={fetchItems} className="ml-3 underline font-medium hover:text-red-900">Retry</button>
          </div>
        )}

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-3 text-gray-500 text-sm">Loading consultations...</span>
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <span className="text-5xl mb-4">💬</span>
              <p className="text-lg font-medium">No consultations found</p>
              <p className="text-sm mt-1">Confirmed or completed appointments will appear here</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Patient</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Doctor</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Time</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Appointment Status</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Notes</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-600">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.appointment_id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-medium text-gray-900">{item.patient_name}</td>
                      <td className="px-4 py-3">
                        <div className="text-gray-700">{item.doctor_name}</div>
                        <div className="text-xs text-gray-400">{item.doctor_specialization}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{formatDate(item.appointment_date)}</td>
                      <td className="px-4 py-3 text-gray-600">{formatTime(item.appointment_time)}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            item.appointment_status === 'COMPLETED' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {item.appointment_status.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {item.has_notes ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                            {item.note_status === 'COMPLETED' ? 'Completed' : 'In Progress'}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-xs">No notes</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => openNoteModal(item)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
                        >
                          {item.has_notes ? 'View / Edit' : 'Add Notes'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {showNoteModal && selectedAppt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b border-gray-200">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Consultation Notes</h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  {selectedAppt.patient_name} · {selectedAppt.doctor_name} · {formatDate(selectedAppt.appointment_date)} {formatTime(selectedAppt.appointment_time)}
                </p>
              </div>
              <button onClick={closeModal} className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-5 space-y-4">
              {noteError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">{noteError}</div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Diagnosis</label>
                <textarea
                  value={noteForm.diagnosis}
                  onChange={(e) => setNoteForm({ ...noteForm, diagnosis: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Diagnosis"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prescriptions</label>
                <textarea
                  value={noteForm.prescriptions}
                  onChange={(e) => setNoteForm({ ...noteForm, prescriptions: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Prescriptions"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={noteForm.notes}
                  onChange={(e) => setNoteForm({ ...noteForm, notes: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Consultation notes"
                />
              </div>
              {note && (
                <AttachmentSection entityType="consultation" entityId={note.id} />
              )}
            </div>
            <div className="flex items-center justify-end gap-3 p-5 border-t border-gray-200">
              <button onClick={closeModal} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                Cancel
              </button>
              <button
                onClick={handleSaveNote}
                disabled={submitting}
                className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
              >
                {submitting ? 'Saving...' : 'Save Notes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
