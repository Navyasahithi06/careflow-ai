import { useState, useEffect } from 'react'
import axios from 'axios'
import type { Payment, PaymentReceipt } from '../../types'

const statusColors: Record<Payment['status'], string> = {
  CREATED: 'bg-blue-100 text-blue-800',
  PENDING: 'bg-gray-100 text-gray-800',
  PAID: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  REFUNDED: 'bg-yellow-100 text-yellow-800',
}

function formatCurrency(amount: number): string {
  return `₹${amount.toFixed(2)}`
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatTime(timeStr: string): string {
  const parts = timeStr.split(':')
  const h = parseInt(parts[0], 10)
  const m = parts[1]
  const period = h >= 12 ? 'PM' : 'AM'
  const hour12 = h % 12 || 12
  return `${hour12}:${m} ${period}`
}

export default function Payment() {
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [receipt, setReceipt] = useState<PaymentReceipt | null>(null)
  const [receiptLoading, setReceiptLoading] = useState(false)
  const [receiptError, setReceiptError] = useState('')

  const token = localStorage.getItem('cf_token')

  useEffect(() => {
    fetchPayments()
  }, [])

  async function fetchPayments() {
    setLoading(true)
    setError('')
    try {
      const res = await axios.get<Payment[]>('/api/payments/my', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setPayments(res.data)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to load payment history.')
      } else {
        setError('An unexpected error occurred.')
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleViewReceipt(paymentId: number) {
    setReceiptLoading(true)
    setReceiptError('')
    setReceipt(null)
    try {
      const res = await axios.get<PaymentReceipt>(`/api/payments/${paymentId}/receipt`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      setReceipt(res.data)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setReceiptError(err.response?.data?.detail || 'Failed to load receipt.')
      } else {
        setReceiptError('An unexpected error occurred.')
      }
    } finally {
      setReceiptLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block w-10 h-10 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
          <p className="mt-3 text-gray-600 text-sm">Loading payment history...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Payment History</h1>
          <p className="mt-1 text-sm text-gray-500">View all your past payments and download receipts.</p>
        </div>

        {error && (
          <div className="mb-6 rounded-lg bg-red-50 border border-red-200 p-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {payments.length === 0 && !error && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">No payments yet</h3>
            <p className="text-sm text-gray-500">You haven&apos;t made any payments. Once you book and attend an appointment, your payment records will appear here.</p>
          </div>
        )}

        {payments.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Doctor</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Specialization</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Appointment</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Time</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Payment Date</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Receipt</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {payments.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{p.doctor_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{p.doctor_specialization}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{formatDate(p.appointment_date)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{formatTime(p.appointment_time)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{formatCurrency(p.amount)}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${statusColors[p.status]}`}>
                          {p.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{formatDate(p.created_at)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {p.status === 'PAID' ? (
                          <button
                            onClick={() => handleViewReceipt(p.id)}
                            className="text-primary-600 hover:text-primary-700 font-medium text-sm underline underline-offset-2"
                          >
                            View Receipt
                          </button>
                        ) : (
                          <span className="text-gray-400 text-xs">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Receipt Modal */}
      {(receipt || receiptLoading || receiptError) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => { setReceipt(null); setReceiptError(''); }} />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-2xl">
              <h2 className="text-lg font-bold text-gray-900">Payment Receipt</h2>
              <button
                onClick={() => { setReceipt(null); setReceiptError(''); }}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="px-6 py-6">
              {receiptLoading && (
                <div className="py-12 text-center">
                  <div className="inline-block w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
                  <p className="mt-3 text-sm text-gray-500">Loading receipt...</p>
                </div>
              )}

              {receiptError && (
                <div className="py-8 text-center">
                  <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-3">
                    <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                    </svg>
                  </div>
                  <p className="text-sm text-red-600">{receiptError}</p>
                </div>
              )}

              {receipt && (
                <div>
                  <div className="text-center mb-6 pb-4 border-b border-dashed border-gray-300">
                    <h3 className="text-xl font-bold text-primary-600">CareFlow AI</h3>
                    <p className="text-xs text-gray-500 mt-1">Payment Receipt</p>
                  </div>

                  <div className="space-y-3 mb-6">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Receipt Number</span>
                      <span className="text-sm font-semibold text-gray-900">{receipt.receipt_number}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Patient Name</span>
                      <span className="text-sm font-medium text-gray-900">{receipt.patient_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Patient Email</span>
                      <span className="text-sm text-gray-700">{receipt.patient_email}</span>
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4 space-y-3 mb-6">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Doctor</span>
                      <span className="text-sm font-medium text-gray-900">{receipt.doctor_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Specialization</span>
                      <span className="text-sm text-gray-700">{receipt.doctor_specialization}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Appointment Date</span>
                      <span className="text-sm text-gray-700">{formatDate(receipt.appointment_date)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Appointment Time</span>
                      <span className="text-sm text-gray-700">{formatTime(receipt.appointment_time)}</span>
                    </div>
                  </div>

                  <div className="border-t border-gray-200 pt-4 space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Consultation Fee</span>
                      <span className="text-sm font-bold text-gray-900">{formatCurrency(receipt.consultation_fee)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Payment ID</span>
                      <span className="text-sm text-gray-700 font-mono">{receipt.payment_id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Payment Date</span>
                      <span className="text-sm text-gray-700">{formatDate(receipt.payment_date)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Payment Status</span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        receipt.payment_status === 'PAID' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {receipt.payment_status}
                      </span>
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-dashed border-gray-300 text-center">
                    <p className="text-xs text-gray-400">This is a system-generated receipt.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
