import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import type { Doctor, DoctorCreate } from '../../types'

const API_BASE = '/api/admin/doctors'
const SPECIALIZATIONS = ['Cardiology', 'General Physician', 'Dermatology', 'Orthopedics', 'Pediatrics', 'Neurology', 'Other']
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

const emptyForm: DoctorCreate = {
  full_name: '',
  specialization: '',
  qualification: '',
  experience_years: 0,
  consultation_fee: 0,
  available_days: '',
  start_time: '09:00',
  end_time: '17:00',
  status: 'active',
}

function formatFee(amount: number): string {
  return `₹${amount.toFixed(2)}`
}

function formatDays(days: string): string {
  if (!days) return '-'
  return days
    .split(',')
    .map((d) => d.trim())
    .filter(Boolean)
    .join(', ')
}

function getAuthHeaders() {
  const token = localStorage.getItem('cf_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export default function Doctors() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [specializationFilter, setSpecializationFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const [showModal, setShowModal] = useState(false)
  const [editingDoctor, setEditingDoctor] = useState<Doctor | null>(null)
  const [form, setForm] = useState<DoctorCreate>({ ...emptyForm })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  const [deleteTarget, setDeleteTarget] = useState<Doctor | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null)

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }, [])

  const fetchDoctors = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params: Record<string, string> = {}
      if (search) params.search = search
      if (specializationFilter) params.specialization = specializationFilter
      if (statusFilter) params.status = statusFilter
      const res = await axios.get(API_BASE, { params, headers: getAuthHeaders() })
      setDoctors(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch doctors')
    } finally {
      setLoading(false)
    }
  }, [search, specializationFilter, statusFilter])

  useEffect(() => {
    fetchDoctors()
  }, [fetchDoctors])

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchDoctors()
    }, 300)
    return () => clearTimeout(timer)
  }, [search, specializationFilter, statusFilter])

  const openAddModal = () => {
    setEditingDoctor(null)
    setForm({ ...emptyForm })
    setFormErrors({})
    setShowModal(true)
  }

  const openEditModal = (doctor: Doctor) => {
    setEditingDoctor(doctor)
    setForm({
      full_name: doctor.full_name,
      specialization: doctor.specialization,
      qualification: doctor.qualification || '',
      experience_years: doctor.experience_years,
      consultation_fee: doctor.consultation_fee,
      available_days: doctor.available_days,
      start_time: doctor.start_time,
      end_time: doctor.end_time,
      status: doctor.status,
    })
    setFormErrors({})
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingDoctor(null)
    setForm({ ...emptyForm })
    setFormErrors({})
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}
    if (!form.full_name.trim()) errors.full_name = 'Name is required'
    if (!form.specialization) errors.specialization = 'Specialization is required'
    if (!form.consultation_fee || form.consultation_fee <= 0) errors.consultation_fee = 'Fee must be greater than 0'
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async () => {
    if (!validateForm()) return
    setSubmitting(true)
    try {
      if (editingDoctor) {
        await axios.put(`${API_BASE}/${editingDoctor.id}`, form, { headers: getAuthHeaders() })
        showToast('Doctor updated successfully')
      } else {
        await axios.post(API_BASE, form, { headers: getAuthHeaders() })
        showToast('Doctor added successfully')
      }
      closeModal()
      fetchDoctors()
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Operation failed'
      showToast(msg, 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const toggleStatus = async (doctor: Doctor) => {
    const newStatus = doctor.status === 'active' ? 'inactive' : 'active'
    try {
      await axios.put(
        `${API_BASE}/${doctor.id}`,
        { ...doctor, status: newStatus },
        { headers: getAuthHeaders() }
      )
      showToast(`Doctor ${newStatus === 'active' ? 'activated' : 'deactivated'} successfully`)
      fetchDoctors()
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to update status', 'error')
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      const res = await axios.delete(`${API_BASE}/${deleteTarget.id}`, { headers: getAuthHeaders() })
      if (res.data.deactivated) {
        showToast('Doctor has been deactivated (has linked appointments)', 'info')
      } else {
        showToast('Doctor deleted successfully')
      }
      setShowDeleteConfirm(false)
      setDeleteTarget(null)
      fetchDoctors()
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to delete doctor', 'error')
    } finally {
      setDeleting(false)
    }
  }

  const handleDayToggle = (day: string) => {
    const currentDays = form.available_days
      ? form.available_days.split(',').map((d) => d.trim()).filter(Boolean)
      : []
    const updated = currentDays.includes(day)
      ? currentDays.filter((d) => d !== day)
      : [...currentDays, day]
    setForm({ ...form, available_days: updated.join(',') })
  }

  const inputClass = (field: string) =>
    `w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 ${
      formErrors[field] ? 'border-red-500' : 'border-gray-300'
    }`

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
            <h1 className="text-2xl font-bold text-gray-900">Doctor Management</h1>
            <p className="text-sm text-gray-500 mt-1">Manage doctors, specializations, and availability</p>
          </div>
          <button
            onClick={openAddModal}
            className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            + Add Doctor
          </button>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
          <div className="p-4 flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search doctors by name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div className="w-full sm:w-48">
              <select
                value={specializationFilter}
                onChange={(e) => setSpecializationFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">All Specializations</option>
                {SPECIALIZATIONS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div className="w-full sm:w-40">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">
            {error}
            <button onClick={fetchDoctors} className="ml-3 underline font-medium hover:text-red-900">
              Retry
            </button>
          </div>
        )}

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-3 text-gray-500 text-sm">Loading doctors...</span>
            </div>
          ) : doctors.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <p className="text-lg font-medium">No doctors found</p>
              <p className="text-sm mt-1">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Specialization</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Qualification</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Experience</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Fee</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Days</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Hours</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {doctors.map((doctor) => (
                    <tr key={doctor.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <span className="font-medium text-gray-900">{doctor.full_name}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-50 text-primary-700">
                          {doctor.specialization}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{doctor.qualification || '-'}</td>
                      <td className="px-4 py-3 text-gray-600">{doctor.experience_years} yrs</td>
                      <td className="px-4 py-3 font-medium text-gray-900">{formatFee(doctor.consultation_fee)}</td>
                      <td className="px-4 py-3 text-gray-600">{formatDays(doctor.available_days)}</td>
                      <td className="px-4 py-3 text-gray-600">
                        {doctor.start_time && doctor.end_time
                          ? `${doctor.start_time} - ${doctor.end_time}`
                          : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            doctor.status === 'active'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {doctor.status === 'active' ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => openEditModal(doctor)}
                            className="p-1.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                            title="Edit"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                              />
                            </svg>
                          </button>
                          <button
                            onClick={() => toggleStatus(doctor)}
                            className={`p-1.5 rounded-lg transition-colors ${
                              doctor.status === 'active'
                                ? 'text-orange-600 hover:bg-orange-50'
                                : 'text-green-600 hover:bg-green-50'
                            }`}
                            title={doctor.status === 'active' ? 'Deactivate' : 'Activate'}
                          >
                            {doctor.status === 'active' ? (
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
                                />
                              </svg>
                            ) : (
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                              </svg>
                            )}
                          </button>
                          <button
                            onClick={() => {
                              setDeleteTarget(doctor)
                              setShowDeleteConfirm(true)
                            }}
                            className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                              />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
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
                {editingDoctor ? 'Edit Doctor' : 'Add New Doctor'}
              </h2>
              <button
                onClick={closeModal}
                className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  className={inputClass('full_name')}
                  placeholder="Dr. John Smith"
                />
                {formErrors.full_name && (
                  <p className="text-red-500 text-xs mt-1">{formErrors.full_name}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Specialization <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.specialization}
                  onChange={(e) => setForm({ ...form, specialization: e.target.value })}
                  className={inputClass('specialization')}
                >
                  <option value="">Select specialization</option>
                  {SPECIALIZATIONS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
                {formErrors.specialization && (
                  <p className="text-red-500 text-xs mt-1">{formErrors.specialization}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Qualification</label>
                <input
                  type="text"
                  value={form.qualification}
                  onChange={(e) => setForm({ ...form, qualification: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="MBBS, MD"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Experience (Years)</label>
                  <input
                    type="number"
                    min={0}
                    value={form.experience_years}
                    onChange={(e) => setForm({ ...form, experience_years: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Consultation Fee <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    min={0.01}
                    step={0.01}
                    value={form.consultation_fee || ''}
                    onChange={(e) => setForm({ ...form, consultation_fee: Number(e.target.value) })}
                    className={inputClass('consultation_fee')}
                    placeholder="800"
                  />
                  {formErrors.consultation_fee && (
                    <p className="text-red-500 text-xs mt-1">{formErrors.consultation_fee}</p>
                  )}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Available Days</label>
                <div className="flex flex-wrap gap-2">
                  {DAYS.map((day) => {
                    const selected = form.available_days
                      .split(',')
                      .map((d) => d.trim())
                      .includes(day)
                    return (
                      <button
                        key={day}
                        type="button"
                        onClick={() => handleDayToggle(day)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                          selected
                            ? 'bg-primary-600 text-white border-primary-600'
                            : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
                        }`}
                      >
                        {day}
                      </button>
                    )
                  })}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                  <input
                    type="time"
                    value={form.start_time}
                    onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">End Time</label>
                  <input
                    type="time"
                    value={form.end_time}
                    onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 p-5 border-t border-gray-200">
              <button
                onClick={closeModal}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
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
                ) : editingDoctor ? (
                  'Update Doctor'
                ) : (
                  'Add Doctor'
                )}
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
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">Delete Doctor</h3>
              <p className="text-sm text-gray-500 text-center mb-6">
                Are you sure you want to delete <strong>{deleteTarget.full_name}</strong>?
                {deleteTarget.status === 'active' && (
                  <span className="block mt-1 text-amber-600">
                    This doctor has an active status and may be deactivated instead.
                  </span>
                )}
              </p>
              <div className="flex items-center justify-center gap-3">
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false)
                    setDeleteTarget(null)
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deleting ? (
                    <span className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Deleting...
                    </span>
                  ) : (
                    'Delete'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}