import { useEffect, useState, useCallback } from 'react'
import axios from 'axios'
import { Appointment, Doctor } from '../../types'

interface Filters {
  search: string
  doctor_id: string
  date: string
  status: string
  payment_status: string
}

const statusColors: Record<string, string> = {
  PENDING_PAYMENT: 'bg-yellow-100 text-yellow-800',
  CONFIRMED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800',
  COMPLETED: 'bg-blue-100 text-blue-800',
}

const paymentStatusColors: Record<string, string> = {
  PENDING: 'bg-gray-100 text-gray-800',
  PAID: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  REFUNDED: 'bg-yellow-100 text-yellow-800',
}

const statusLabels: Record<string, string> = {
  PENDING_PAYMENT: 'Pending Payment',
  CONFIRMED: 'Confirmed',
  CANCELLED: 'Cancelled',
  COMPLETED: 'Completed',
}

const paymentStatusLabels: Record<string, string> = {
  PENDING: 'Pending',
  PAID: 'Paid',
  FAILED: 'Failed',
  REFUNDED: 'Refunded',
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(amount)
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function formatTime(timeStr: string): string {
  if (!timeStr) return '-'
  return timeStr
}

function buildQueryString(filters: Filters): string {
  const params = new URLSearchParams()
  if (filters.search) params.append('search', filters.search)
  if (filters.doctor_id) params.append('doctor_id', filters.doctor_id)
  if (filters.date) params.append('date', filters.date)
  if (filters.status) params.append('status', filters.status)
  if (filters.payment_status) params.append('payment_status', filters.payment_status)
  return params.toString()
}

export default function AdminAppointments() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>('')
  const [filters, setFilters] = useState<Filters>({
    search: '',
    doctor_id: '',
    date: '',
    status: '',
    payment_status: '',
  })

  const fetchAppointments = useCallback(async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('cf_token')
      const queryString = buildQueryString(filters)
      const url = queryString
        ? `/api/admin/appointments?${queryString}`
        : '/api/admin/appointments'
      const response = await axios.get<Appointment[]>(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setAppointments(response.data)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch appointments')
      } else {
        setError('Failed to fetch appointments')
      }
    } finally {
      setLoading(false)
    }
  }, [filters])

  const fetchDoctors = async () => {
    try {
      const token = localStorage.getItem('cf_token')
      const response = await axios.get<Doctor[]>('/api/admin/doctors', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setDoctors(response.data)
    } catch {
      // Doctors dropdown is optional - non-critical
    }
  }

  useEffect(() => {
    fetchDoctors()
  }, [])

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchAppointments()
    }, 300)
    return () => clearTimeout(debounceTimer)
  }, [fetchAppointments])

  const handleFilterChange = (field: keyof Filters, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const clearFilters = () => {
    setFilters({
      search: '',
      doctor_id: '',
      date: '',
      status: '',
      payment_status: '',
    })
  }

  const hasActiveFilters = Object.values(filters).some((v) => v !== '')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-cyan-900">Appointments</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage and monitor all patient appointments across the platform.
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">Filters</h2>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="text-sm text-cyan-600 hover:text-cyan-800 font-medium transition-colors"
              >
                Clear all filters
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div>
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
                Search Patient
              </label>
              <input
                id="search"
                type="text"
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                placeholder="Patient name..."
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
              />
            </div>

            {/* Doctor Filter */}
            <div>
              <label htmlFor="doctor" className="block text-sm font-medium text-gray-700 mb-1">
                Doctor
              </label>
              <select
                id="doctor"
                value={filters.doctor_id}
                onChange={(e) => handleFilterChange('doctor_id', e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
              >
                <option value="">All Doctors</option>
                {doctors.map((doctor) => (
                  <option key={doctor.id} value={doctor.id}>
                    {doctor.full_name} ({doctor.specialization})
                  </option>
                ))}
              </select>
            </div>

            {/* Date Filter */}
            <div>
              <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-1">
                Date
              </label>
              <input
                id="date"
                type="date"
                value={filters.date}
                onChange={(e) => handleFilterChange('date', e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
              />
            </div>

            {/* Status Filter */}
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                id="status"
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
              >
                <option value="">All Status</option>
                <option value="PENDING_PAYMENT">Pending Payment</option>
                <option value="CONFIRMED">Confirmed</option>
                <option value="CANCELLED">Cancelled</option>
                <option value="COMPLETED">Completed</option>
              </select>
            </div>

            {/* Payment Status Filter */}
            <div>
              <label htmlFor="payment_status" className="block text-sm font-medium text-gray-700 mb-1">
                Payment Status
              </label>
              <select
                id="payment_status"
                value={filters.payment_status}
                onChange={(e) => handleFilterChange('payment_status', e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
              >
                <option value="">All Payment Status</option>
                <option value="PENDING">Pending</option>
                <option value="PAID">Paid</option>
                <option value="FAILED">Failed</option>
                <option value="REFUNDED">Refunded</option>
              </select>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Loading */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="w-12 h-12 border-4 border-cyan-200 border-t-cyan-600 rounded-full animate-spin mb-4"></div>
            <p className="text-sm text-gray-500">Loading appointments...</p>
          </div>
        ) : appointments.length === 0 ? (
          /* Empty State */
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <h3 className="mt-3 text-lg font-medium text-gray-900">No appointments found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {hasActiveFilters
                ? 'Try adjusting your filters to see more results.'
                : 'There are no appointments in the system yet.'}
            </p>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-cyan-600 hover:bg-cyan-700 transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>
        ) : (
          /* Table */
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <p className="text-sm text-gray-500">
                Showing <span className="font-medium text-gray-900">{appointments.length}</span> appointment{appointments.length !== 1 ? 's' : ''}
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Patient
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Doctor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Specialization
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Fee
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Appointment Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Payment Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {appointments.map((appointment) => (
                    <tr
                      key={appointment.id}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {appointment.patient_name}
                        </div>
                        <div className="text-xs text-gray-500">ID: {appointment.patient_id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{appointment.doctor_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700">
                          {appointment.doctor_specialization}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {formatDate(appointment.appointment_date)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {formatTime(appointment.appointment_time)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {formatCurrency(appointment.consultation_fee)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            statusColors[appointment.status] || 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {statusLabels[appointment.status] || appointment.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            paymentStatusColors[appointment.payment_status] || 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {paymentStatusLabels[appointment.payment_status] || appointment.payment_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
