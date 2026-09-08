import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import type { MedicalRecord, MedicalRecordCreate, AdminPatient } from '../../types'
import AttachmentSection from '../../components/AttachmentSection'

const API_BASE = '/api/admin/medical-records'
const PATIENTS_API = '/api/admin/patients'
const RECORD_TYPES = ['DIAGNOSIS', 'PRESCRIPTION', 'LAB_REPORT', 'GENERAL']

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

const emptyForm: MedicalRecordCreate = {
  patient_id: 0,
  doctor_id: null,
  record_type: 'GENERAL',
  title: '',
  diagnosis: '',
  prescriptions: '',
  notes: '',
}

export default function MedicalRecords() {
  const [records, setRecords] = useState<MedicalRecord[]>([])
  const [patients, setPatients] = useState<AdminPatient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  const [showModal, setShowModal] = useState(false)
  const [editingRecord, setEditingRecord] = useState<MedicalRecord | null>(null)
  const [form, setForm] = useState<MedicalRecordCreate>({ ...emptyForm })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  const [deleteTarget, setDeleteTarget] = useState<MedicalRecord | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null)

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }, [])

  const fetchRecords = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params: Record<string, string> = {}
      if (search) params.search = search
      if (typeFilter) params.type = typeFilter
      const res = await axios.get(API_BASE, { params, headers: getAuthHeaders() })
      setRecords(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch records')
    } finally {
      setLoading(false)
    }
  }, [search, typeFilter])

  const fetchPatients = useCallback(async () => {
    try {
      const res = await axios.get(PATIENTS_API, { headers: getAuthHeaders() })
      setPatients(res.data)
    } catch {
      setPatients([])
    }
  }, [])

  useEffect(() => {
    fetchRecords()
    fetchPatients()
  }, [fetchRecords, fetchPatients])

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchRecords()
    }, 300)
    return () => clearTimeout(timer)
  }, [search, typeFilter])

  const openAddModal = () => {
    setEditingRecord(null)
    setForm({ ...emptyForm, patient_id: patients[0]?.id || 0 })
    setFormErrors({})
    setShowModal(true)
  }

  const openEditModal = (record: MedicalRecord) => {
    setEditingRecord(record)
    setForm({
      patient_id: record.patient_id,
      doctor_id: record.doctor_id ?? null,
      record_type: record.record_type,
      title: record.title,
      diagnosis: record.diagnosis || '',
      prescriptions: record.prescriptions || '',
      notes: record.notes || '',
    })
    setFormErrors({})
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingRecord(null)
    setForm({ ...emptyForm })
    setFormErrors({})
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}
    if (!form.patient_id) errors.patient_id = 'Patient is required'
    if (!form.title.trim()) errors.title = 'Title is required'
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async () => {
    if (!validateForm()) return
    setSubmitting(true)
    try {
      if (editingRecord) {
        await axios.put(`${API_BASE}/${editingRecord.id}`, form, { headers: getAuthHeaders() })
        showToast('Medical record updated successfully')
      } else {
        await axios.post(API_BASE, form, { headers: getAuthHeaders() })
        showToast('Medical record added successfully')
      }
      closeModal()
      fetchRecords()
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Operation failed', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await axios.delete(`${API_BASE}/${deleteTarget.id}`, { headers: getAuthHeaders() })
      showToast('Medical record deleted successfully')
      setShowDeleteConfirm(false)
      setDeleteTarget(null)
      fetchRecords()
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to delete record', 'error')
    } finally {
      setDeleting(false)
    }
  }

  const inputClass = (field: string) =>
    `w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 ${
      formErrors[field] ? 'border-red-500' : 'border-gray-300'
    }`

  const typeBadge = (type: string) => {
    const styles: Record<string, string> = {
      DIAGNOSIS: 'bg-blue-100 text-blue-800',
      PRESCRIPTION: 'bg-green-100 text-green-800',
      LAB_REPORT: 'bg-purple-100 text-purple-800',
      GENERAL: 'bg-gray-100 text-gray-800',
    }
    return styles[type] || 'bg-gray-100 text-gray-800'
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
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Medical Records</h1>
            <p className="text-sm text-gray-500 mt-1">Manage patient medical records, diagnoses, and prescriptions</p>
          </div>
          <button
            onClick={openAddModal}
            className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            + Add Record
          </button>
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
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">All Types</option>
                {RECORD_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">
            {error}
            <button onClick={fetchRecords} className="ml-3 underline font-medium hover:text-red-900">Retry</button>
          </div>
        )}

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-3 text-gray-500 text-sm">Loading records...</span>
            </div>
          ) : records.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <span className="text-5xl mb-4">📁</span>
              <p className="text-lg font-medium">No medical records found</p>
              <p className="text-sm mt-1">Add a record to get started</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Patient</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Title</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Type</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Doctor</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((record) => (
                    <>
                      <tr key={record.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 font-medium text-gray-900">{record.patient_name}</td>
                        <td className="px-4 py-3">
                          <div className="font-medium text-gray-900">{record.title}</div>
                          {record.diagnosis && <div className="text-xs text-gray-500">{record.diagnosis}</div>}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${typeBadge(record.record_type)}`}>
                            {record.record_type}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-600">{record.doctor_name || '-'}</td>
                        <td className="px-4 py-3 text-gray-600">{formatDate(record.created_at)}</td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => setExpandedId(expandedId === record.id ? null : record.id)}
                              className="p-1.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                              title="Attachments"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                              </svg>
                            </button>
                            <button
                              onClick={() => openEditModal(record)}
                              className="p-1.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                              title="Edit"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                            <button
                              onClick={() => { setDeleteTarget(record); setShowDeleteConfirm(true) }}
                              className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                              title="Delete"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </td>
                      </tr>
                      {expandedId === record.id && (
                        <tr key={`${record.id}-att`} className="border-b border-gray-100 bg-gray-50/50">
                          <td colSpan={6} className="px-4 py-3">
                            <AttachmentSection entityType="medical_record" entityId={record.id} />
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                {editingRecord ? 'Edit Medical Record' : 'Add Medical Record'}
              </h2>
              <button onClick={closeModal} className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Patient <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.patient_id}
                  onChange={(e) => setForm({ ...form, patient_id: Number(e.target.value) })}
                  className={inputClass('patient_id')}
                  disabled={!!editingRecord}
                >
                  <option value={0}>Select patient</option>
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>{p.full_name} ({p.email})</option>
                  ))}
                </select>
                {formErrors.patient_id && <p className="text-red-500 text-xs mt-1">{formErrors.patient_id}</p>}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Record Type</label>
                  <select
                    value={form.record_type}
                    onChange={(e) => setForm({ ...form, record_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    {RECORD_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Doctor ID</label>
                  <input
                    type="number"
                    min={1}
                    value={form.doctor_id || ''}
                    onChange={(e) => setForm({ ...form, doctor_id: e.target.value ? Number(e.target.value) : null })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Optional"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className={inputClass('title')}
                  placeholder="e.g. Initial Consultation, Blood Test Report"
                />
                {formErrors.title && <p className="text-red-500 text-xs mt-1">{formErrors.title}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Diagnosis</label>
                <textarea
                  value={form.diagnosis}
                  onChange={(e) => setForm({ ...form, diagnosis: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Diagnosis details"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prescriptions</label>
                <textarea
                  value={form.prescriptions}
                  onChange={(e) => setForm({ ...form, prescriptions: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Prescribed medications"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Additional notes"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 p-5 border-t border-gray-200">
              <button onClick={closeModal} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? (
                  <span className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Saving...
                  </span>
                ) : editingRecord ? 'Update Record' : 'Add Record'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteConfirm && deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
            <div className="p-6">
              <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-red-100 rounded-full">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">Delete Medical Record</h3>
              <p className="text-sm text-gray-500 text-center mb-6">
                Are you sure you want to delete <strong>{deleteTarget.title}</strong> for <strong>{deleteTarget.patient_name}</strong>?
              </p>
              <div className="flex items-center justify-center gap-3">
                <button onClick={() => { setShowDeleteConfirm(false); setDeleteTarget(null) }} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                  Cancel
                </button>
                <button onClick={handleDelete} disabled={deleting} className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50">
                  {deleting ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
