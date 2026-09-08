export interface User {
  id: number
  email: string
  full_name: string
  phone?: string
  role: 'patient' | 'admin'
  is_active: number
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  role: string
  user_id: number
  full_name: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  full_name: string
  password: string
  phone?: string
}

export interface Doctor {
  id: number
  full_name: string
  specialization: string
  qualification?: string
  experience_years: number
  consultation_fee: number
  available_days: string
  start_time: string
  end_time: string
  status: 'active' | 'inactive'
  created_at: string
}

export interface DoctorCreate {
  full_name: string
  specialization: string
  qualification?: string
  experience_years: number
  consultation_fee: number
  available_days: string
  start_time: string
  end_time: string
  status: string
}

export interface Appointment {
  id: number
  patient_id: number
  doctor_id: number
  appointment_date: string
  appointment_time: string
  status: 'PENDING_PAYMENT' | 'CONFIRMED' | 'CANCELLED' | 'COMPLETED'
  payment_status: 'PENDING' | 'PAID' | 'FAILED' | 'REFUNDED'
  consultation_fee: number
  doctor_name: string
  doctor_specialization: string
  patient_name: string
  created_at: string
}

export interface AppointmentCreate {
  doctor_id: number
  appointment_date: string
  appointment_time: string
}

export interface Payment {
  id: number
  appointment_id: number
  patient_id: number
  doctor_id: number
  amount: number
  currency: string
  gateway: string
  gateway_order_id?: string
  gateway_payment_id?: string
  status: 'CREATED' | 'PENDING' | 'PAID' | 'FAILED' | 'REFUNDED'
  doctor_name: string
  doctor_specialization: string
  patient_name: string
  appointment_date: string
  appointment_time: string
  created_at: string
}

export interface PaymentOrder {
  payment_id: number
  appointment_id: number
  gateway_order_id: string
  amount: number
  currency: string
  razorpay_key_id: string
}

export interface PaymentReceipt {
  receipt_number: string
  patient_name: string
  patient_email: string
  doctor_name: string
  doctor_specialization: string
  appointment_id: number
  appointment_date: string
  appointment_time: string
  consultation_fee: number
  payment_id: number
  payment_date: string
  payment_status: string
  currency: string
}

export interface Token {
  id: number
  appointment_id: number
  patient_id: number
  doctor_id: number
  queue_date: string
  token_number: number
  status: 'WAITING' | 'CALLED' | 'IN_CONSULTATION' | 'COMPLETED' | 'SKIPPED' | 'CANCELLED'
  doctor_name: string
  doctor_specialization: string
  patient_name: string
  appointment_time: string
  created_at: string
}

export interface QueueStatus {
  doctor_id: number
  doctor_name: string
  queue_date: string
  current_token: number | null
  currently_called: number | null
  total_waiting: number
  total_completed: number
  total_in_consultation: number
  total_skipped: number
  total_cancelled: number
  queue_status: string
  estimated_wait_minutes: number
  tokens: Token[]
}

export interface SymptomAnalysisResult {
  analysis_id: number
  detected_symptoms: string[]
  recommended_specialization: string
  recommendation_reason: string
  urgency: 'ROUTINE' | 'PRIORITY' | 'URGENT'
  warning_signs: string[]
  matching_doctors: Doctor[]
  disclaimer: string
}

export interface SymptomAnalysisHistory {
  id: number
  input_text: string
  detected_symptoms: string[]
  recommended_specialization: string
  recommendation_reason: string
  urgency: string
  ai_model?: string
  created_at: string
}

export interface AdminPatient {
  id: number
  email: string
  full_name: string
  phone?: string
  is_active: number
  created_at: string
  appointment_count: number
}

export type MedicalRecordType = 'DIAGNOSIS' | 'PRESCRIPTION' | 'LAB_REPORT' | 'GENERAL'

export interface MedicalRecord {
  id: number
  patient_id: number
  doctor_id?: number | null
  record_type: MedicalRecordType
  title: string
  diagnosis?: string | null
  prescriptions?: string | null
  notes?: string | null
  created_by: number
  patient_name: string
  doctor_name?: string | null
  created_at: string
  updated_at?: string | null
}

export interface MedicalRecordCreate {
  patient_id: number
  doctor_id?: number | null
  record_type: string
  title: string
  diagnosis?: string
  prescriptions?: string
  notes?: string
}

export interface ConsultationNote {
  id: number
  appointment_id: number
  patient_id: number
  doctor_id: number
  status: string
  notes?: string | null
  diagnosis?: string | null
  prescriptions?: string | null
  created_by: number
  patient_name: string
  doctor_name: string
  doctor_specialization: string
  appointment_date: string
  appointment_time: string
  created_at: string
  updated_at?: string | null
}

export interface ConsultationListItem {
  appointment_id: number
  patient_id: number
  doctor_id: number
  patient_name: string
  doctor_name: string
  doctor_specialization: string
  appointment_date: string
  appointment_time: string
  appointment_status: string
  payment_status: string
  has_notes: boolean
  note_id?: number | null
  note_status?: string | null
}

export interface ReportOverview {
  total_patients: number
  total_doctors: number
  total_appointments: number
  total_confirmed_appointments: number
  total_completed_consultations: number
  total_revenue: number
  collection_today: number
  appointments_today: number
}

export interface AppointmentTrendItem {
  date: string
  total: number
  confirmed: number
  completed: number
}

export interface RevenueTrendItem {
  date: string
  revenue: number
}

export interface DoctorStat {
  doctor_id: number
  doctor_name: string
  specialization: string
  appointment_count: number
  completed_count: number
}

export interface ReportAppointmentsResponse {
  trends: AppointmentTrendItem[]
  by_doctor: DoctorStat[]
}

export interface ReportRevenueResponse {
  trends: RevenueTrendItem[]
}

export interface ForecastDayItem {
  date: string
  weekday: string
  forecast: number
  low: number
  high: number
}

export interface HistoryDayItem {
  date: string
  count: number
}

export interface DemandForecast {
  sufficient_historical_data: boolean
  data_points: number
  total_appointments: number
  history_start: string
  history_end: string
  history: HistoryDayItem[]
  forecast: ForecastDayItem[]
  notice?: string | null
}

export interface DoctorUtilizationItem {
  doctor_id: number
  doctor_name: string
  specialization: string
  avg_daily_booked: number
  worked_days: number
  capacity_per_day: number
  historical_utilization_pct: number
  predicted_utilization_pct: number
  forecast_appointments: number
  status: 'OVERBOOKED' | 'HIGH' | 'MODERATE' | 'LOW' | 'NO_ACTIVITY'
  notice?: string | null
}

export interface UtilizationForecast {
  consultation_slot_minutes: number
  capacity_formula: string
  doctors: DoctorUtilizationItem[]
  notice?: string | null
}

export interface MethodologyInfo {
  demand_model: string
  demand_description: string
  utilization_formula: string
  disclaimer: string
}

export interface PredictionsResponse {
  generated_at: string
  methodology: MethodologyInfo
  demand: DemandForecast
  doctor_utilization: UtilizationForecast
}

export interface HistoryTimelineEntry {
  type: 'medical_record' | 'consultation'
  id: number
  title: string
  record_type: string
  doctor_name: string | null
  diagnosis?: string | null
  prescriptions?: string | null
  notes?: string | null
  created_at: string
}

export type AttachmentEntityType = 'medical_record' | 'consultation'

export interface Attachment {
  id: number
  file_name: string
  mime_type: string
  size_bytes: number
  uploaded_by?: number
  created_at: string
}

export type NotificationType =
  | 'appointment_confirmed'
  | 'payment_success'
  | 'token_called'
  | 'consultation_completed'
  | 'new_patient_registered'

export interface AppNotification {
  id: number
  recipient_id: number
  title: string
  message: string
  notification_type: NotificationType
  reference_id?: number | null
  is_read: boolean
  read_at?: string | null
  created_at: string
}
