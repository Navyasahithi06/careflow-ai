import { useState, useEffect, useCallback, useMemo } from 'react'
import axios from 'axios'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
} from 'recharts'
import type { ReportOverview, ReportAppointmentsResponse, ReportRevenueResponse, PredictionsResponse } from '../../types'

function getAuthHeaders() {
  const token = localStorage.getItem('cf_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function defaultStart() {
  const d = new Date()
  d.setDate(d.getDate() - 30)
  return d.toISOString().slice(0, 10)
}

const currency = (n: number) =>
  `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function AdminReports() {
  const [overview, setOverview] = useState<ReportOverview | null>(null)
  const [apptReport, setApptReport] = useState<ReportAppointmentsResponse | null>(null)
  const [revReport, setRevReport] = useState<ReportRevenueResponse | null>(null)
  const [predictions, setPredictions] = useState<PredictionsResponse | null>(null)
  const [predLoading, setPredLoading] = useState(false)
  const [predError, setPredError] = useState('')
  const [horizon, setHorizon] = useState(7)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [startDate, setStartDate] = useState(defaultStart)
  const [endDate, setEndDate] = useState(todayStr)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = { start: startDate, end: endDate }
      const headers = getAuthHeaders()
      const [ov, ap, rev] = await Promise.all([
        axios.get<ReportOverview>('/api/admin/reports/overview', { params, headers }),
        axios.get<ReportAppointmentsResponse>('/api/admin/reports/appointments', { params, headers }),
        axios.get<ReportRevenueResponse>('/api/admin/reports/revenue', { params, headers }),
      ])
      setOverview(ov.data)
      setApptReport(ap.data)
      setRevReport(rev.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch reports')
    } finally {
      setLoading(false)
    }
  }, [startDate, endDate])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const fetchPredictions = useCallback(async () => {
    setPredLoading(true)
    setPredError('')
    try {
      const params = { start: startDate, end: endDate, horizon_days: horizon }
      const headers = getAuthHeaders()
      const res = await axios.get<PredictionsResponse>('/api/admin/reports/predictions', { params, headers })
      setPredictions(res.data)
    } catch (err: any) {
      setPredError(err.response?.data?.detail || err.message || 'Failed to fetch predictions')
    } finally {
      setPredLoading(false)
    }
  }, [startDate, endDate, horizon])

  useEffect(() => {
    fetchPredictions()
  }, [fetchPredictions])

  const applyRange = () => {
    if (startDate && endDate && startDate > endDate) {
      setError('Start date cannot be after end date')
      return
    }
    fetchAll()
  }

  const demandData = useMemo(() => {
    if (!predictions) return []
    return [
      ...(predictions.demand.history || []).map((h) => ({ date: h.date, historical: h.count })),
      ...(predictions.demand.forecast || []).map((f) => ({ date: f.date, forecast: f.forecast, low: f.low, high: f.high })),
    ]
  }, [predictions])

  const statusStyles: Record<string, string> = {
    OVERBOOKED: 'bg-red-100 text-red-700',
    HIGH: 'bg-amber-100 text-amber-700',
    MODERATE: 'bg-blue-100 text-blue-700',
    LOW: 'bg-green-100 text-green-700',
    NO_ACTIVITY: 'bg-gray-100 text-gray-600',
  }

  const statusColors: Record<string, string> = {
    OVERBOOKED: '#ef4444',
    HIGH: '#f59e0b',
    MODERATE: '#3b82f6',
    LOW: '#10b981',
    NO_ACTIVITY: '#9ca3af',
  }

  const statCards = [
    { label: 'Total Patients', value: overview?.total_patients ?? '-', icon: '👥', color: 'bg-blue-50 text-blue-600' },
    { label: 'Total Doctors', value: overview?.total_doctors ?? '-', icon: '🩺', color: 'bg-teal-50 text-teal-600' },
    { label: 'Appointments', value: overview?.total_appointments ?? '-', icon: '📅', color: 'bg-indigo-50 text-indigo-600' },
    { label: 'Completed', value: overview?.total_completed_consultations ?? '-', icon: '✅', color: 'bg-green-50 text-green-600' },
    { label: 'Total Revenue', value: overview ? currency(overview.total_revenue) : '-', icon: '💰', color: 'bg-emerald-50 text-emerald-600' },
    { label: "Collection Today", value: overview ? currency(overview.collection_today) : '-', icon: '📈', color: 'bg-purple-50 text-purple-600' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports & Analytics</h1>
        <p className="text-gray-500 mt-1">Hospital performance, appointments, and revenue overview</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 flex flex-col sm:flex-row gap-3 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Start Date</label>
          <input
            type="date"
            value={startDate}
            max={endDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">End Date</label>
          <input
            type="date"
            value={endDate}
            min={startDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Forecast Horizon</label>
          <select
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 w-full sm:w-auto"
          >
            <option value={3}>3 days</option>
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
        </div>
        <button
          onClick={applyRange}
          className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
        >
          Apply
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
          <button onClick={fetchAll} className="ml-3 underline font-medium hover:text-red-900">Retry</button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-gray-500 text-sm">Loading reports...</span>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            {statCards.map((card) => (
              <div key={card.label} className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-xl ${card.color}`}>
                  {card.icon}
                </div>
                <p className="mt-3 text-2xl font-bold text-gray-900">{card.value}</p>
                <p className="text-xs text-gray-500 mt-0.5">{card.label}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">Appointment Trend</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={apptReport?.trends || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Area type="monotone" dataKey="total" name="Total" stroke="#6366f1" fill="#6366f1" fillOpacity={0.15} />
                    <Area type="monotone" dataKey="confirmed" name="Confirmed" stroke="#10b981" fill="#10b981" fillOpacity={0.15} />
                    <Area type="monotone" dataKey="completed" name="Completed" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.15} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">Revenue Trend</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={revReport?.trends || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${v}`} />
                    <Tooltip formatter={(v: any) => [`₹${Number(v).toLocaleString('en-IN')}`, 'Revenue']} />
                    <Line type="monotone" dataKey="revenue" name="Revenue" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Appointments by Doctor</h3>
            {apptReport && apptReport.by_doctor.length > 0 ? (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={apptReport.by_doctor} layout="vertical" margin={{ left: 8, right: 16 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                    <YAxis type="category" dataKey="doctor_name" width={160} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="appointment_count" name="Appointments" fill="#6366f1" radius={[0, 4, 4, 0]} />
                    <Bar dataKey="completed_count" name="Completed" fill="#10b981" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-gray-400 text-sm py-10 text-center">No appointment data in selected range</p>
            )}
          </div>

          {apptReport && apptReport.by_doctor.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700">Doctor Performance</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50">
                      <th className="text-left px-5 py-3 font-medium text-gray-600">Doctor</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-600">Specialization</th>
                      <th className="text-right px-5 py-3 font-medium text-gray-600">Appointments</th>
                      <th className="text-right px-5 py-3 font-medium text-gray-600">Completed</th>
                      <th className="text-right px-5 py-3 font-medium text-gray-600">Completion Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apptReport.by_doctor.map((d) => {
                      const rate = d.appointment_count > 0 ? Math.round((d.completed_count / d.appointment_count) * 100) : 0
                      return (
                        <tr key={d.doctor_id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="px-5 py-3 font-medium text-gray-900">{d.doctor_name}</td>
                          <td className="px-5 py-3 text-gray-600">{d.specialization}</td>
                          <td className="px-5 py-3 text-right text-gray-700">{d.appointment_count}</td>
                          <td className="px-5 py-3 text-right text-gray-700">{d.completed_count}</td>
                          <td className="px-5 py-3 text-right">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                              {rate}%
                            </span>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <h2 className="text-xl font-bold text-gray-900 pt-2">Demand & Utilization Forecasts</h2>

          {predLoading ? (
            <div className="flex items-center justify-center py-16 bg-white rounded-xl border border-gray-200 shadow-sm">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-3 text-gray-500 text-sm">Loading predictions...</span>
            </div>
          ) : predError ? (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {predError}
              <button onClick={fetchPredictions} className="ml-3 underline font-medium hover:text-red-900">Retry</button>
            </div>
          ) : predictions ? (
            <>
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
                <p className="font-semibold text-blue-900 mb-1">About these forecasts</p>
                <p className="text-blue-800/90">{predictions.methodology.demand_description}</p>
                <p className="text-blue-800/90 mt-1">{predictions.methodology.utilization_formula}</p>
                <p className="text-blue-700 mt-2 text-xs font-medium">
                  {predictions.methodology.disclaimer}
                </p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-gray-700">Appointment Demand Forecast</h3>
                {predictions.demand.forecast.length > 0 && (
                  <p className="text-xs text-gray-500 mt-1">
                    Forecast period: {predictions.demand.forecast[0].date} to{' '}
                    {predictions.demand.forecast[predictions.demand.forecast.length - 1].date} · {horizon} days · Based
                    on {predictions.demand.total_appointments} appointments across {predictions.demand.data_points}{' '}
                    historical days
                  </p>
                )}
                <div className="mt-4">
                  {predictions.demand.sufficient_historical_data ? (
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={demandData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                          <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                          <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                          <Tooltip />
                          <Legend wrapperStyle={{ fontSize: 12 }} />
                          <Bar dataKey="historical" name="Historical" fill="#6366f1" fillOpacity={0.3} />
                          <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#ef4444" strokeWidth={2} dot={{ r: 3, fill: '#ef4444' }} />
                          <Line type="monotone" dataKey="low" name="Lower band" stroke="#fca5a5" strokeDasharray="4 4" dot={false} />
                          <Line type="monotone" dataKey="high" name="Upper band" stroke="#fca5a5" strokeDasharray="4 4" dot={false} />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="py-10 text-center">
                      <p className="inline-block text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
                        {predictions.demand.notice || 'Not enough historical appointment data to produce a meaningful forecast.'}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-gray-700">Doctor Utilization Forecast</h3>
                <p className="text-xs text-gray-500 mt-1">
                  Predicted utilization assumes each doctor's historical booking rate (share of daily{' '}
                  {predictions.doctor_utilization.consultation_slot_minutes}-minute slot capacity) persists into the
                  forecast window.
                </p>
                {predictions.doctor_utilization.doctors.length > 0 ? (
                  <>
                    <div className="h-80 mt-4">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={predictions.doctor_utilization.doctors} layout="vertical" margin={{ left: 8, right: 16 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
                          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                          <YAxis type="category" dataKey="doctor_name" width={170} tick={{ fontSize: 11 }} />
                          <Tooltip formatter={(v: any) => [`${v}%`, 'Predicted utilization']} />
                          <Legend wrapperStyle={{ fontSize: 12 }} />
                          <Bar dataKey="predicted_utilization_pct" name="Predicted utilization (%)" radius={[0, 4, 4, 0]}>
                            {predictions.doctor_utilization.doctors.map((d) => (
                              <Cell key={d.doctor_id} fill={statusColors[d.status]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="overflow-x-auto mt-4">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-gray-200 bg-gray-50">
                            <th className="text-left px-4 py-3 font-medium text-gray-600">Doctor</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-600">Avg / Day</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-600">Working Days</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-600">Daily Capacity</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-600">Utilization</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-600">Forecast Appts</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {predictions.doctor_utilization.doctors.map((d) => (
                            <tr key={d.doctor_id} className="border-b border-gray-100 hover:bg-gray-50">
                              <td className="px-4 py-3 font-medium text-gray-900">{d.doctor_name}</td>
                              <td className="px-4 py-3 text-right text-gray-700">{d.avg_daily_booked}</td>
                              <td className="px-4 py-3 text-right text-gray-700">{d.worked_days}</td>
                              <td className="px-4 py-3 text-right text-gray-700">{d.capacity_per_day}</td>
                              <td className="px-4 py-3 text-right text-gray-700">{d.predicted_utilization_pct}%</td>
                              <td className="px-4 py-3 text-right text-gray-700">{d.forecast_appointments}</td>
                              <td className="px-4 py-3 text-right">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusStyles[d.status]}`}>
                                  {d.status.replace('_', ' ')}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : (
                  <p className="text-gray-400 text-sm py-10 text-center">No doctor data in selected range</p>
                )}
              </div>
            </>
          ) : null}
        </>
      )}
    </div>
  )
}
