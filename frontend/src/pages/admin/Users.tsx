import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import type { AdminPatient } from '../../types'

const API_BASE = '/api/admin/patients'

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

export default function Users() {
  const [patients, setPatients] = useState<AdminPatient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null)

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }, [])

  const fetchPatients = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params: Record<string, string> = {}
      if (search) params.search = search
      if (statusFilter === 'active') params.active = 'true'
      if (statusFilter === 'inactive') params.active = 'false'
      const res = await axios.get(API_BASE, { params, headers: getAuthHeaders() })
      setPatients(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch patients')
    } finally {
      setLoading(false)
    }
  }, [search, statusFilter])

  useEffect(() => {
    fetchPatients()
  }, [fetchPatients])

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchPatients()
    }, 300)
    return () => clearTimeout(timer)
  }, [search, statusFilter])

  const toggleStatus = async (patient: AdminPatient) => {
    const newStatus = patient.is_active ? 0 : 1
    try {
      await axios.put(
        `${API_BASE}/${patient.id}/status`,
        { is_active: newStatus },
        { headers: getAuthHeaders() }
      )
      showToast(`${patient.full_name} ${newStatus ? 'activated' : 'deactivated'} successfully`)
      fetchPatients()
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to update status', 'error')
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
          <h1 className="text-2xl font-bold text-gray-900">Patient Management</h1>
          <p className="text-sm text-gray-500 mt-1">View, search, and manage patient accounts</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
          <div className="p-4 flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search patients by name or email..."
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
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">
            {error}
            <button onClick={fetchPatients} className="ml-3 underline font-medium hover:text-red-900">
              Retry
            </button>
          </div>
        )}

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-3 text-gray-500 text-sm">Loading patients...</span>
            </div>
          ) : patients.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <span className="text-5xl mb-4">👥</span>
              <p className="text-lg font-medium">No patients found</p>
              <p className="text-sm mt-1">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Patient</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Phone</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Appointments</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Joined</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {patients.map((patient) => (
                    <tr key={patient.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-primary-700 font-bold text-xs">
                            {patient.full_name.charAt(0).toUpperCase()}
                          </div>
                          <span className="font-medium text-gray-900">{patient.full_name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{patient.email}</td>
                      <td className="px-4 py-3 text-gray-600">{patient.phone || '-'}</td>
                      <td className="px-4 py-3 text-gray-600">{patient.appointment_count}</td>
                      <td className="px-4 py-3 text-gray-600">{formatDate(patient.created_at)}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            patient.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {patient.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => toggleStatus(patient)}
                          className={`p-1.5 rounded-lg transition-colors ${
                            patient.is_active ? 'text-orange-600 hover:bg-orange-50' : 'text-green-600 hover:bg-green-50'
                          }`}
                          title={patient.is_active ? 'Deactivate' : 'Activate'}
                        >
                          {patient.is_active ? (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                            </svg>
                          ) : (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          )}
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
    </div>
  )
}
