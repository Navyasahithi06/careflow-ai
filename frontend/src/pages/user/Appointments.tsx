import { useEffect, useState, useCallback } from 'react'
import axios from 'axios'
import { Appointment, PaymentOrder, Token } from '../../types'

declare global {
  interface Window {
    Razorpay: any
  }
}

interface RazorpayResponse {
  razorpay_order_id: string
  razorpay_payment_id: string
  razorpay_signature: string
}

const statusColors: Record<string, string> = {
  PENDING_PAYMENT: 'bg-amber-100 text-amber-800 border border-amber-200',
  CONFIRMED: 'bg-green-100 text-green-800 border border-green-200',
  CANCELLED: 'bg-red-100 text-red-800 border border-red-200',
  COMPLETED: 'bg-blue-100 text-blue-800 border border-blue-200',
}

const paymentStatusColors: Record<string, string> = {
  PENDING: 'bg-gray-100 text-gray-800 border border-gray-200',
  PAID: 'bg-green-100 text-green-800 border border-green-200',
  FAILED: 'bg-red-100 text-red-800 border border-red-200',
  REFUNDED: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
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

export default function Appointments() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [processingPayment, setProcessingPayment] = useState<number | null>(null)
  const [cancellingId, setCancellingId] = useState<number | null>(null)
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false)
  const [appointmentToCancel, setAppointmentToCancel] = useState<Appointment | null>(null)
  const [successMessage, setSuccessMessage] = useState('')
  const [tokens, setTokens] = useState<Record<number, Token>>({})

  const token = localStorage.getItem('cf_token')

  const fetchTokens = useCallback(async (appts: Appointment[]) => {
    const tokenMap: Record<number, Token> = {}
    for (const appt of appts) {
      if (appt.status === 'CONFIRMED' || appt.status === 'COMPLETED') {
        try {
          const res = await axios.get(`/api/tokens/appointment/${appt.id}`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          tokenMap[appt.id] = res.data
        } catch {
          // Token may not exist yet
        }
      }
    }
    setTokens(tokenMap)
  }, [token])

  const fetchAppointments = useCallback(async () => {
    try {
      setLoading(true)
      setError('')
      const response = await axios.get('/api/appointments/my', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setAppointments(response.data)
      fetchTokens(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load appointments. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    fetchAppointments()
  }, [fetchAppointments])

  const handleCancelClick = (appointment: Appointment) => {
    setAppointmentToCancel(appointment)
    setCancelDialogOpen(true)
  }

  const handleCancelConfirm = async () => {
    if (!appointmentToCancel) return
    setCancellingId(appointmentToCancel.id)
    try {
      await axios.put(`/api/appointments/${appointmentToCancel.id}/cancel`, null, {
        headers: { Authorization: `Bearer ${token}` },
      })
      setAppointments((prev) =>
        prev.map((appt) =>
          appt.id === appointmentToCancel.id ? { ...appt, status: 'CANCELLED' as const } : appt
        )
      )
      setSuccessMessage('Appointment cancelled successfully.')
      setTimeout(() => setSuccessMessage(''), 5000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to cancel appointment. Please try again.')
    } finally {
      setCancellingId(null)
      setCancelDialogOpen(false)
      setAppointmentToCancel(null)
    }
  }

  const handleCancelDialogClose = () => {
    setCancelDialogOpen(false)
    setAppointmentToCancel(null)
  }

  const handlePay = async (appointment: Appointment) => {
    setProcessingPayment(appointment.id)
    setError('')
    try {
      const orderResponse = await axios.post(
        '/api/payments/create-order',
        { appointment_id: appointment.id },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      const orderData: PaymentOrder = orderResponse.data

      const userName = localStorage.getItem('cf_user_name') || 'Patient'

      const options = {
        key: orderData.razorpay_key_id,
        amount: orderData.amount * 100,
        currency: orderData.currency,
        name: 'CareFlow AI',
        description: `Consultation Fee - Dr. ${appointment.doctor_name}`,
        order_id: orderData.gateway_order_id,
        handler: async (response: RazorpayResponse) => {
          try {
            await axios.post(
              '/api/payments/verify',
              {
                appointment_id: appointment.id,
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              },
              { headers: { Authorization: `Bearer ${token}` } }
            )
            setSuccessMessage('Payment successful! Your appointment is confirmed.')
            setTimeout(() => setSuccessMessage(''), 5000)
            await fetchAppointments()
          } catch (err: any) {
            setError(
              err.response?.data?.detail ||
                'Payment verification failed. Please contact support.'
            )
          }
        },
        prefill: { name: userName },
        theme: { color: '#2563eb' },
        modal: {
          ondismiss: () => {
            setError('Payment was cancelled. You can retry when ready.')
            setTimeout(() => setError(''), 5000)
          },
        },
      }

      const rzp = new window.Razorpay(options)
      rzp.open()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initiate payment. Please try again.')
    } finally {
      setProcessingPayment(null)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-IN', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatFee = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-600 text-sm">Loading appointments...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">My Appointments</h1>
          <p className="mt-1 text-sm text-gray-500">
            View and manage your upcoming and past appointments.
          </p>
        </div>

        {successMessage && (
          <div className="mb-6 rounded-lg bg-green-50 border border-green-200 p-4 flex items-center gap-3">
            <svg className="w-5 h-5 text-green-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm font-medium text-green-800">{successMessage}</p>
          </div>
        )}

        {error && (
          <div className="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 flex items-center gap-3">
            <svg className="w-5 h-5 text-red-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        )}

        {appointments.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <svg className="mx-auto w-16 h-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <h3 className="mt-4 text-lg font-semibold text-gray-900">No appointments yet</h3>
            <p className="mt-2 text-sm text-gray-500 max-w-sm mx-auto">
              You haven't booked any appointments yet. Book a consultation with a doctor to get started.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {appointments.map((appt) => (
              <div
                key={appt.id}
                className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
              >
                <div className="p-6">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                          <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-base font-semibold text-gray-900">Dr. {appt.doctor_name}</h3>
                          <p className="text-sm text-gray-500">{appt.doctor_specialization}</p>
                        </div>
                      </div>

                      <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <span>{formatDate(appt.appointment_date)}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span>{appt.appointment_time}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="font-medium text-gray-900">{formatFee(appt.consultation_fee)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col items-start sm:items-end gap-2 flex-shrink-0">
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            statusColors[appt.status] || 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {statusLabels[appt.status] || appt.status}
                        </span>
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            paymentStatusColors[appt.payment_status] || 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {paymentStatusLabels[appt.payment_status] || appt.payment_status}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 mt-2">
                        {appt.status === 'PENDING_PAYMENT' && (
                          <button
                            onClick={() => handlePay(appt)}
                            disabled={processingPayment === appt.id}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {processingPayment === appt.id ? (
                              <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                Processing...
                              </>
                            ) : (
                              <>
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                                </svg>
                                Pay Consultation Fee
                              </>
                            )}
                          </button>
                        )}

                        {appt.status === 'CONFIRMED' && tokens[appt.id] && (
                          <a
                            href="/user/token"
                            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-primary-600 bg-primary-50 border border-primary-200 rounded-lg hover:bg-primary-100 transition-colors"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                            </svg>
                            Token #{tokens[appt.id].token_number}
                          </a>
                        )}

                        {(appt.status === 'PENDING_PAYMENT' || appt.status === 'CONFIRMED') && (
                          <button
                            onClick={() => handleCancelClick(appt)}
                            disabled={cancellingId === appt.id}
                            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-red-600 bg-white border border-red-300 rounded-lg hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {cancellingId === appt.id ? (
                              <div className="w-4 h-4 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            )}
                            Cancel
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {cancelDialogOpen && appointmentToCancel && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
              className="fixed inset-0 bg-black/50 transition-opacity"
              onClick={handleCancelDialogClose}
            />
            <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                  <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Cancel Appointment</h3>
                  <p className="text-sm text-gray-500">This action cannot be undone.</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-6">
                Are you sure you want to cancel your appointment with{' '}
                <span className="font-medium">Dr. {appointmentToCancel.doctor_name}</span> on{' '}
                <span className="font-medium">{formatDate(appointmentToCancel.appointment_date)}</span> at{' '}
                <span className="font-medium">{appointmentToCancel.appointment_time}</span>?
              </p>
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={handleCancelDialogClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Keep Appointment
                </button>
                <button
                  onClick={handleCancelConfirm}
                  disabled={cancellingId !== null}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {cancellingId !== null ? 'Cancelling...' : 'Yes, Cancel'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
