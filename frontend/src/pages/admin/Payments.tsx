import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import type { Payment, Doctor } from '../../types'

interface Filters {
  search: string
  doctor_id: string
  status: string
  date: string
}

const statusColors: Record<string, string> = {
  CREATED: 'bg-blue-100 text-blue-800',
  PENDING: 'bg-gray-100 text-gray-800',
  PAID: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  REFUNDED: 'bg-yellow-100 text-yellow-800',
}

const statusOptions = ['CREATED', 'PENDING', 'PAID', 'FAILED', 'REFUNDED']

function formatCurrency(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency || 'INR',
      minimumFractionDigits: 2,
    }).format(amount)
  } catch {
    return `₹${amount.toFixed(2)}`
  }
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

function buildQueryString(filters: Filters): string {
  const params = new URLSearchParams()
  if (filters.search) params.append('search', filters.search)
  if (filters.doctor_id) params.append('doctor_id', filters.doctor_id)
  if (filters.status) params.append('status', filters.status)
  if (filters.date) params.append('date', filters.date)
  return params.toString()
}

function getAuthHeaders() {
  const token = localStorage.getItem('cf_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export default function AdminPayments() {
  const [payments, setPayments] = useState<Payment[]>([])
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>('')
  const [filters, setFilters] = useState<Filters>({
    search: '',
    doctor_id: '',
    status: '',
    date: '',
  })

  const fetchPayments = useCallback(async () => {
    try {
      setLoading(true)
      setError('')
      const queryString = buildQueryString(filters)
      const url = queryString ? `/api/admin/payments?${queryString}` : '/api/admin/payments'
      const response = await axios.get<Payment[]>(url, { headers: getAuthHeaders() })
      setPayments(response.data)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch payments')
      } else {
        setError('Failed to fetch payments')
      }
    } finally {
      setLoading(false)
    }
  }, [filters])

  const fetchDoctors = async () => {
    try {
      const response = await axios.get<Doctor[]>('/api/admin/doctors', { headers: getAuthHeaders() })
      setDoctors(response.data)
    } catch {
      // Non-critical
    }
  }

  useEffect(() => {
    fetchDoctors()
  }, [])

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchPayments()
    }, 300)
    return () => clearTimeout(debounceTimer)
  }, [fetchPayments])

  const handleFilterChange = (field: keyof Filters, value: string) => {
    setFilters((prev) => ({ ...prev, [field]: value }))
  }

  const clearFilters = () => {
    setFilters({ search: '', doctor_id: '', status: '', date: '' })
  }

  const hasActiveFilters = Object.values(filters).some((v) => v !== '')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-primary-600">Payment Management</h1>
          <p className="mt-2 text-sm text-gray-600">
            View and manage all payment transactions across the platform.
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">Filters</h2>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="text-sm text-primary-600 hover:text-primary-800 font-medium transition-colors"
              >
                Clear all filters
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
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
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              >
                <option value="">All Doctors</option>
                {doctors.map((doctor) => (
                  <option key={doctor.id} value={doctor.id}>
                    {doctor.full_name} ({doctor.specialization})
                  </option>
                ))}
              </select>
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
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              >
                <option value="">All Status</option>
                {statusOptions.map((status) => (
                  <option key={status} value={status}>
                    {status.charAt(0) + status.slice(1).toLowerCase()}
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
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              />
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
            <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mb-4"></div>
            <p className="text-sm text-gray-500">Loading payments...</p>
          </div>
        ) : payments.length === 0 ? (
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
                d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
              />
            </svg>
            <h3 className="mt-3 text-lg font-medium text-gray-900">No payments found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {hasActiveFilters
                ? 'Try adjusting your filters to see more results.'
                : 'There are no payment records in the system yet.'}
            </p>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-primary-600 hover:bg-primary-700 transition-colors"
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
                Showing <span className="font-medium text-gray-900">{payments.length}</span> payment{payments.length !== 1 ? 's' : ''}
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      ID
                    </th>
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
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Currency
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Gateway
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Payment ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {payments.map((payment) => (
                    <tr
                      key={payment.id}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">#{payment.id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{payment.patient_name}</div>
                        <div className="text-xs text-gray-500">ID: {payment.patient_id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{payment.doctor_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700">{payment.doctor_specialization}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {formatCurrency(payment.amount, payment.currency)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-600">{payment.currency}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            statusColors[payment.status] || 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {payment.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700">{payment.gateway}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-xs text-gray-500 font-mono">
                          {payment.gateway_payment_id || payment.gateway_order_id || '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{formatDate(payment.created_at)}</div>
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