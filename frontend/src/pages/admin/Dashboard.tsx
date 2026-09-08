import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import StatsCard from '../../components/StatsCard'
import type { Appointment, Payment } from '../../types'

const API_BASE = import.meta.env.VITE_API_URL || ''

function getAuthHeaders() {
  const token = localStorage.getItem('cf_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function formatCurrency(amount: number) {
  return `₹${amount.toLocaleString()}`
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function formatTime(timeStr: string) {
  const [h, m] = timeStr.split(':')
  const hour = parseInt(h, 10)
  const suffix = hour >= 12 ? 'PM' : 'AM'
  const display = hour % 12 || 12
  return `${display}:${m} ${suffix}`
}

function getTodayDate() {
  return new Date().toISOString().split('T')[0]
}

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good Morning'
  if (hour < 17) return 'Good Afternoon'
  return 'Good Evening'
}

function getStatusBadge(status: Appointment['status']) {
  const styles: Record<string, string> = {
    PENDING_PAYMENT: 'bg-yellow-100 text-yellow-800',
    CONFIRMED: 'bg-green-100 text-green-800',
    CANCELLED: 'bg-red-100 text-red-800',
    COMPLETED: 'bg-blue-100 text-blue-800',
  }
  return styles[status] || 'bg-gray-100 text-gray-800'
}

function getPaymentBadge(status: Appointment['payment_status']) {
  const styles: Record<string, string> = {
    PENDING: 'bg-yellow-100 text-yellow-800',
    PAID: 'bg-green-100 text-green-800',
    FAILED: 'bg-red-100 text-red-800',
    REFUNDED: 'bg-purple-100 text-purple-800',
  }
  return styles[status] || 'bg-gray-100 text-gray-800'
}

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const today = getTodayDate()

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      try {
        const [apptRes, payRes] = await Promise.all([
          axios.get<Appointment[]>(`${API_BASE}/api/admin/appointments`, {
            params: { date: today },
            headers: getAuthHeaders(),
          }),
          axios.get<Payment[]>(`${API_BASE}/api/admin/payments`, {
            params: { date: today },
            headers: getAuthHeaders(),
          }),
        ])
        setAppointments(apptRes.data)
        setPayments(payRes.data)
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          setError(err.response?.data?.message || 'Failed to load dashboard data.')
        } else {
          setError('An unexpected error occurred.')
        }
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [today])

  const totalAppointments = appointments.length
  const confirmedCount = appointments.filter((a) => a.status === 'CONFIRMED').length
  const totalPayments = payments.length
  const totalRevenue = payments.reduce((sum, p) => sum + p.amount, 0)

  const recentAppointments = [...appointments]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-500 text-sm">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="bg-red-50 border border-red-200 rounded-xl p-8 text-center max-w-md">
          <p className="text-red-600 font-medium text-lg">Something went wrong</p>
          <p className="text-red-500 mt-2 text-sm">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {getGreeting()}, Admin
          </h1>
          <p className="text-gray-500 mt-1">Here's what's happening at the hospital today.</p>
        </div>
        <div className="text-sm text-gray-500 bg-white px-4 py-2 rounded-lg border border-gray-200">
          {formatDate(today)}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Today's Appointments"
          value={totalAppointments}
          icon="📅"
          color="bg-blue-50 text-blue-600"
        />
        <StatsCard
          title="Confirmed Appointments"
          value={confirmedCount}
          icon="✅"
          color="bg-green-50 text-green-600"
        />
        <StatsCard
          title="Total Payments"
          value={totalPayments}
          icon="💳"
          color="bg-purple-50 text-purple-600"
        />
        <StatsCard
          title="Revenue"
          value={formatCurrency(totalRevenue)}
          icon="💰"
          color="bg-orange-50 text-orange-600"
        />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Recent Appointments</h2>
        </div>
        {recentAppointments.length === 0 ? (
          <div className="p-8 text-center text-gray-400">No appointments today.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left text-gray-500 uppercase text-xs tracking-wider">
                  <th className="px-6 py-3 font-medium">Patient</th>
                  <th className="px-6 py-3 font-medium">Doctor</th>
                  <th className="px-6 py-3 font-medium">Date</th>
                  <th className="px-6 py-3 font-medium">Time</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium">Payment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {recentAppointments.map((appt) => (
                  <tr key={appt.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">{appt.patient_name}</td>
                    <td className="px-6 py-4 text-gray-700">
                      <div>{appt.doctor_name}</div>
                      <div className="text-xs text-gray-400">{appt.doctor_specialization}</div>
                    </td>
                    <td className="px-6 py-4 text-gray-700">{formatDate(appt.appointment_date)}</td>
                    <td className="px-6 py-4 text-gray-700">{formatTime(appt.appointment_time)}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(appt.status)}`}>
                        {appt.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${getPaymentBadge(appt.payment_status)}`}>
                        {appt.payment_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Links</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            onClick={() => navigate('/admin/doctors')}
            className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors text-left"
          >
            <span className="text-2xl">👨‍⚕️</span>
            <div>
              <p className="font-medium text-gray-900 text-sm">Manage Doctors</p>
              <p className="text-xs text-gray-400">Add, edit, remove doctors</p>
            </div>
          </button>
          <button
            onClick={() => navigate('/admin/appointments')}
            className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors text-left"
          >
            <span className="text-2xl">📋</span>
            <div>
              <p className="font-medium text-gray-900 text-sm">View Appointments</p>
              <p className="text-xs text-gray-400">All scheduled appointments</p>
            </div>
          </button>
          <button
            onClick={() => navigate('/admin/queue')}
            className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors text-left"
          >
            <span className="text-2xl">🔢</span>
            <div>
              <p className="font-medium text-gray-900 text-sm">Queue Management</p>
              <p className="text-xs text-gray-400">Monitor and manage queue</p>
            </div>
          </button>
          <button
            onClick={() => navigate('/admin/payments')}
            className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors text-left"
          >
            <span className="text-2xl">💰</span>
            <div>
              <p className="font-medium text-gray-900 text-sm">Payment History</p>
              <p className="text-xs text-gray-400">View all transactions</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  )
}
