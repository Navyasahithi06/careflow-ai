import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

function getAuthHeaders() {
  const token = localStorage.getItem('cf_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

interface SettingsData {
  notification_preferences: {
    new_patient_registered: boolean
    payment_received: boolean
    appointment_confirmed: boolean
    consultation_completed: boolean
    token_called: boolean
  }
  ai: {
    symptom_analysis_enabled: boolean
    model: string
    ollama_available: boolean
  }
  system: {
    application: string
    environment: string
    api_version: string
    database: string
    utc_time: string
  }
}

const PREFERENCE_LABELS: Array<{ key: keyof SettingsData['notification_preferences']; label: string }> = [
  { key: 'new_patient_registered', label: 'New patient registered' },
  { key: 'payment_received', label: 'Payment received' },
  { key: 'appointment_confirmed', label: 'Appointment / payment confirmation' },
  { key: 'consultation_completed', label: 'Consultation completed' },
  { key: 'token_called', label: 'Token called' },
]

function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
        checked ? 'bg-primary-600' : 'bg-gray-300'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  )
}

function InfoRow({ label, value, tone }: { label: string; value: string; tone?: 'ok' | 'warn' | 'muted' }) {
  const color =
    tone === 'ok'
      ? 'text-green-700'
      : tone === 'warn'
      ? 'text-amber-700'
      : tone === 'muted'
      ? 'text-gray-400'
      : 'text-gray-800'
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className={`text-sm font-medium ${color}`}>{value}</span>
    </div>
  )
}

export default function AdminSettings() {
  const [data, setData] = useState<SettingsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')

  const fetchSettings = useCallback(async () => {
    setLoading(true)
    setError('')
    setSaveMsg('')
    try {
      const res = await axios.get<SettingsData>('/api/admin/settings', { headers: getAuthHeaders() })
      setData(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load settings')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  const updatePref = (key: keyof SettingsData['notification_preferences'], value: boolean) => {
    if (!data) return
    setData({ ...data, notification_preferences: { ...data.notification_preferences, [key]: value } })
    setSaveMsg('')
  }

  const setSymptomEnabled = (value: boolean) => {
    if (!data) return
    setData({ ...data, ai: { ...data.ai, symptom_analysis_enabled: value } })
    setSaveMsg('')
  }

  const handleSave = async () => {
    if (!data) return
    setSaving(true)
    setSaveMsg('')
    setError('')
    try {
      const res = await axios.put<SettingsData>(
        '/api/admin/settings',
        {
          notification_preferences: data.notification_preferences,
          ai: { symptom_analysis_enabled: data.ai.symptom_analysis_enabled },
        },
        { headers: getAuthHeaders() },
      )
      setData(res.data)
      setSaveMsg('Settings saved successfully.')
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">System, AI, and notification preferences</p>
      </div>

      {error && (
        <div className="flex items-center justify-between bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          <span>{error}</span>
          <button onClick={fetchSettings} className="ml-3 underline font-medium hover:text-red-900">
            Retry
          </button>
        </div>
      )}

      {saveMsg && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">{saveMsg}</div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-gray-500 text-sm">Loading settings...</span>
        </div>
      ) : data ? (
        <>
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h2 className="text-lg font-semibold text-gray-900 mb-1">Notification Preferences</h2>
            <p className="text-sm text-gray-500 mb-4">
              Control which notification types are delivered to patients and admins.
            </p>
            {PREFERENCE_LABELS.map((pref) => (
              <div
                key={pref.key}
                className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0"
              >
                <span className="text-sm text-gray-700">{pref.label}</span>
                <Toggle checked={data.notification_preferences[pref.key]} onChange={(v) => updatePref(pref.key, v)} />
              </div>
            ))}
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h2 className="text-lg font-semibold text-gray-900 mb-1">AI Settings</h2>
            <p className="text-sm text-gray-500 mb-4">AI symptom analysis configuration.</p>

            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <div className="text-sm text-gray-700">AI Symptom Analysis</div>
                <div className="text-xs text-gray-400">Enables or disables Ollama-based symptom analysis for patients.</div>
              </div>
              <Toggle checked={data.ai.symptom_analysis_enabled} onChange={setSymptomEnabled} />
            </div>

            <div className="pt-2">
              <InfoRow label="Configured model" value={data.ai.model} />
              <InfoRow
                label="Ollama status"
                value={data.ai.ollama_available ? 'Available' : 'Unavailable'}
                tone={data.ai.ollama_available ? 'ok' : 'warn'}
              />
            </div>
            <p className="text-[11px] text-gray-400 mt-3">
              The AI model is read-only and managed by the administrator at the infrastructure level.
            </p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h2 className="text-lg font-semibold text-gray-900 mb-1">System Information</h2>
            <p className="text-sm text-gray-500 mb-3">General application status (non-sensitive).</p>
            <InfoRow label="Application" value={data.system.application} />
            <InfoRow label="Environment" value={data.system.environment} />
            <InfoRow label="API version" value={data.system.api_version} />
            <InfoRow
              label="Database"
              value={data.system.database === 'ok' ? 'Connected' : 'Unreachable'}
              tone={data.system.database === 'ok' ? 'ok' : 'warn'}
            />
            <InfoRow label="Server time (UTC)" value={new Date(data.system.utc_time).toLocaleString()} tone="muted" />
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-5 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
            <button
              onClick={fetchSettings}
              disabled={saving}
              className="px-5 py-2 text-sm font-medium rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Discard changes
            </button>
          </div>
        </>
      ) : null}
    </div>
  )
}