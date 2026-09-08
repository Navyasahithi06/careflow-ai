import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import {
  SymptomAnalysisResult,
  SymptomAnalysisHistory,
  Doctor,
  AppointmentCreate,
} from '../../types'

const getAuthHeaders = () => {
  const token = localStorage.getItem('cf_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const getTodayStr = (): string => {
  const d = new Date()
  return d.toISOString().split('T')[0]
}

const formatDays = (days: string): string => {
  if (!days) return 'N/A'
  const dayMap: Record<string, string> = {
    Mon: 'Monday',
    Tue: 'Tuesday',
    Wed: 'Wednesday',
    Thu: 'Thursday',
    Fri: 'Friday',
    Sat: 'Saturday',
    Sun: 'Sunday',
  }
  return days
    .split(',')
    .map((d) => dayMap[d.trim()] || d.trim())
    .join(', ')
}

const formatFee = (fee: number): string => {
  return `₹${Number(fee).toFixed(2)}`
}

const formatDateTime = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const urgencyConfig: Record<string, { color: string; bg: string; border: string; label: string; icon: string }> = {
  ROUTINE: {
    color: 'text-green-800',
    bg: 'bg-green-50',
    border: 'border-green-200',
    label: 'ROUTINE',
    icon: '🟢',
  },
  PRIORITY: {
    color: 'text-amber-800',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    label: 'PRIORITY',
    icon: '🟡',
  },
  URGENT: {
    color: 'text-red-800',
    bg: 'bg-red-50',
    border: 'border-red-200',
    label: 'URGENT',
    icon: '🔴',
  },
}

export default function UserSymptoms() {
  const navigate = useNavigate()
  const [symptoms, setSymptoms] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<SymptomAnalysisResult | null>(null)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<SymptomAnalysisHistory[]>([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [expandedHistoryId, setExpandedHistoryId] = useState<number | null>(null)

  const [modalOpen, setModalOpen] = useState(false)
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null)
  const [apptDate, setApptDate] = useState(getTodayStr())
  const [apptTime, setApptTime] = useState('')
  const [bookingLoading, setBookingLoading] = useState(false)
  const [bookingError, setBookingError] = useState('')
  const [bookingSuccess, setBookingSuccess] = useState(false)

  const fetchHistory = useCallback(async () => {
    try {
      setHistoryLoading(true)
      const response = await axios.get('/api/ai/symptom-analysis/my', {
        headers: getAuthHeaders(),
      })
      setHistory(response.data)
    } catch {
    } finally {
      setHistoryLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory])

  const handleAnalyze = async () => {
    const trimmed = symptoms.trim()
    if (!trimmed) {
      setError('Please describe your symptoms before analyzing.')
      return
    }

    setAnalyzing(true)
    setError('')
    setResult(null)

    try {
      const response = await axios.post(
        '/api/ai/symptom-analysis',
        { symptoms: trimmed },
        { headers: getAuthHeaders() }
      )
      setResult(response.data)
      fetchHistory()
    } catch (err: any) {
      if (err.response?.status === 503 || err.code === 'ECONNREFUSED' || err.message?.includes('Network Error')) {
        setError(
          'AI service is temporarily unavailable. Please try again or select a specialist manually.'
        )
      } else {
        setError(err.response?.data?.detail || 'Failed to analyze symptoms. Please try again.')
      }
    } finally {
      setAnalyzing(false)
    }
  }

  const openBookingModal = (doctor: Doctor) => {
    setSelectedDoctor(doctor)
    setApptDate(getTodayStr())
    setApptTime('')
    setBookingError('')
    setBookingSuccess(false)
    setModalOpen(true)
  }

  const closeBookingModal = () => {
    setModalOpen(false)
    setSelectedDoctor(null)
  }

  const handleBookAppointment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedDoctor) return

    setBookingError('')
    setBookingLoading(true)
    setBookingSuccess(false)

    try {
      const payload: AppointmentCreate = {
        doctor_id: selectedDoctor.id,
        appointment_date: apptDate,
        appointment_time: apptTime,
      }

      await axios.post('/api/appointments', payload, {
        headers: getAuthHeaders(),
      })

      setBookingSuccess(true)
      setTimeout(() => {
        closeBookingModal()
        navigate('/user/appointments')
      }, 1500)
    } catch (err: any) {
      setBookingError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          err.message ||
          'Failed to book appointment.'
      )
    } finally {
      setBookingLoading(false)
    }
  }

  const urgency = result ? urgencyConfig[result.urgency] || urgencyConfig.ROUTINE : null

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Symptom Analysis</h1>
          <p className="mt-1 text-sm text-gray-500">
            Describe your symptoms and get AI-powered analysis and specialist recommendations.
          </p>
        </div>

        <div className="mb-6 rounded-lg bg-amber-50 border border-amber-200 p-4 flex items-start gap-3">
          <svg className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-amber-800">
            This AI assistant provides general guidance and is not a medical diagnosis. Always consult a qualified healthcare professional for medical advice.
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <label className="block text-sm font-semibold text-gray-900 mb-2">
            Describe your symptoms
          </label>
          <textarea
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            placeholder="e.g. I have been experiencing a persistent headache for the last 3 days, along with mild fever and sensitivity to light..."
            rows={5}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none resize-none text-sm leading-relaxed"
          />
          <div className="mt-4 flex items-center justify-between">
            <button
              onClick={handleAnalyze}
              disabled={analyzing || !symptoms.trim()}
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-primary-600 text-white text-sm font-semibold rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {analyzing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Analyzing your symptoms...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Analyze Symptoms
                </>
              )}
            </button>
          </div>
        </div>

        {analyzing && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 flex flex-col items-center gap-4 mb-8">
            <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-600 font-medium">Analyzing your symptoms...</p>
            <p className="text-sm text-gray-400">This may take a moment while the AI processes your input.</p>
          </div>
        )}

        {error && (
          <div className="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 flex items-start gap-3">
            <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-red-800">{error}</p>
              <button
                onClick={() => navigate('/user/doctors')}
                className="mt-2 text-sm font-semibold text-primary-600 hover:text-primary-700 underline underline-offset-2"
              >
                Browse doctors manually →
              </button>
            </div>
          </div>
        )}

        {result && urgency && (
          <div className="mb-8">
            {result.urgency === 'URGENT' && (
              <div className="mb-4 rounded-lg bg-red-600 p-4 flex items-center gap-3">
                <svg className="w-6 h-6 text-white flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="font-bold text-white">Urgent medical attention may be needed</p>
                  <p className="text-sm text-red-100">Please seek immediate medical care.</p>
                </div>
              </div>
            )}

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">Detected Symptoms</h3>
                  <div className="flex flex-wrap gap-2">
                    {result.detected_symptoms.map((symptom, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-primary-50 text-primary-700 border border-primary-200"
                      >
                        {symptom}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-6">
                  <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">Recommended Specialist</h3>
                  <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">🩺</span>
                      <span className="text-lg font-bold text-primary-800">{result.recommended_specialization}</span>
                    </div>
                    <p className="text-sm text-primary-700">{result.recommendation_reason}</p>
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-6">
                  <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">Urgency Level</h3>
                  <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border ${urgency.bg} ${urgency.border}`}>
                    <span>{urgency.icon}</span>
                    <span className={`font-bold text-sm ${urgency.color}`}>{urgency.label}</span>
                  </div>
                </div>

                {result.warning_signs.length > 0 && (
                  <div className="border-t border-gray-100 pt-6">
                    <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">⚠️ Warning Signs</h3>
                    <ul className="space-y-2">
                      {result.warning_signs.map((sign, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-red-700">
                          <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {sign}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="border-t border-gray-100 pt-6">
                  <p className="text-xs text-gray-400 flex items-center gap-1.5">
                    <span>ℹ️</span>
                    {result.disclaimer || 'This AI assistant provides general guidance and does not provide a medical diagnosis.'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {result && result.matching_doctors.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Matching Doctors</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.matching_doctors.map((doctor) => (
                <div
                  key={doctor.id}
                  className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow flex flex-col"
                >
                  <div className="p-5 flex-1">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                          <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-base font-semibold text-gray-900">Dr. {doctor.full_name}</h3>
                          <p className="text-sm text-primary-600 font-medium">{doctor.specialization}</p>
                        </div>
                      </div>
                    </div>

                    {doctor.qualification && (
                      <p className="text-sm text-gray-600 mb-1.5 flex items-center gap-1.5">
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path d="M12 14l9-5-9-5-9 5 9 5z" />
                          <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                        </svg>
                        {doctor.qualification}
                      </p>
                    )}

                    <p className="text-sm text-gray-600 mb-1.5 flex items-center gap-1.5">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      {doctor.experience_years} year{doctor.experience_years !== 1 ? 's' : ''} experience
                    </p>

                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-sm text-gray-500">Consultation Fee</span>
                        <span className="text-base font-bold text-primary-700">
                          {formatFee(doctor.consultation_fee)}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 text-sm text-gray-600 mb-1">
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <span>{formatDays(doctor.available_days)}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-sm text-gray-600">
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>{doctor.start_time || 'N/A'} - {doctor.end_time || 'N/A'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 border-t border-gray-100 bg-gray-50">
                    <button
                      onClick={() => openBookingModal(doctor)}
                      className="w-full py-2.5 px-4 bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold rounded-lg transition-colors"
                    >
                      Book Appointment
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-lg font-bold text-gray-900">Analysis History</h2>
            <p className="text-sm text-gray-500 mt-1">Your previous symptom analyses.</p>
          </div>

          {historyLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : history.length === 0 ? (
            <div className="py-12 text-center">
              <svg className="mx-auto w-12 h-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="mt-3 text-sm text-gray-500">No analysis history yet.</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {history.map((item) => {
                const histUrgency = urgencyConfig[item.urgency] || urgencyConfig.ROUTINE
                const isExpanded = expandedHistoryId === item.id

                return (
                  <div key={item.id} className="p-4 hover:bg-gray-50 transition-colors">
                    <button
                      onClick={() => setExpandedHistoryId(isExpanded ? null : item.id)}
                      className="w-full text-left"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-900 font-medium truncate">
                            {item.input_text.length > 120
                              ? item.input_text.substring(0, 120) + '...'
                              : item.input_text}
                          </p>
                          <div className="flex items-center gap-3 mt-2">
                            <span className="text-xs font-medium text-primary-600">
                              {item.recommended_specialization}
                            </span>
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${histUrgency.bg} ${histUrgency.color} border ${histUrgency.border}`}>
                              {histUrgency.icon} {histUrgency.label}
                            </span>
                            <span className="text-xs text-gray-400">
                              {formatDateTime(item.created_at)}
                            </span>
                          </div>
                        </div>
                        <svg
                          className={`w-5 h-5 text-gray-400 flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
                        <div>
                          <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Full Input</p>
                          <p className="text-sm text-gray-700">{item.input_text}</p>
                        </div>
                        {item.detected_symptoms.length > 0 && (
                          <div>
                            <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Detected Symptoms</p>
                            <div className="flex flex-wrap gap-1.5">
                              {item.detected_symptoms.map((s, i) => (
                                <span key={i} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-primary-50 text-primary-700 border border-primary-200">
                                  {s}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        <div>
                          <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Recommendation Reason</p>
                          <p className="text-sm text-gray-700">{item.recommendation_reason}</p>
                        </div>
                        {item.ai_model && (
                          <div>
                            <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">AI Model</p>
                            <p className="text-sm text-gray-600">{item.ai_model}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {modalOpen && selectedDoctor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={closeBookingModal}
          />
          <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md z-10">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">Book Appointment</h2>
                <button
                  onClick={closeBookingModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="bg-primary-50 rounded-lg p-4 mb-6">
                <p className="font-semibold text-gray-900">Dr. {selectedDoctor.full_name}</p>
                <p className="text-sm text-gray-600">{selectedDoctor.specialization}</p>
                <p className="text-sm font-medium text-primary-700 mt-1">
                  Consultation Fee: {formatFee(selectedDoctor.consultation_fee)}
                </p>
              </div>

              {bookingSuccess ? (
                <div className="text-center py-6">
                  <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Appointment Booked!</h3>
                  <p className="text-gray-600">Redirecting to your appointments...</p>
                </div>
              ) : (
                <form onSubmit={handleBookAppointment}>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Appointment Date
                    </label>
                    <input
                      type="date"
                      min={getTodayStr()}
                      value={apptDate}
                      onChange={(e) => setApptDate(e.target.value)}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none"
                    />
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Appointment Time
                    </label>
                    <input
                      type="time"
                      value={apptTime}
                      onChange={(e) => setApptTime(e.target.value)}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none"
                    />
                  </div>

                  {bookingError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                      <p className="text-red-700 text-sm">{bookingError}</p>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={bookingLoading}
                    className="w-full py-2.5 px-4 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    {bookingLoading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                        Booking...
                      </>
                    ) : (
                      'Confirm Booking'
                    )}
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
