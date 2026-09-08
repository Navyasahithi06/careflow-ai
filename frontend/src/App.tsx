import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import UserLayout from './layouts/UserLayout'
import AdminLayout from './layouts/AdminLayout'

// User pages
import UserLogin from './pages/user/Login'
import UserRegister from './pages/user/Register'
import UserDashboard from './pages/user/Dashboard'
import UserSymptoms from './pages/user/Symptoms'
import UserDoctors from './pages/user/Doctors'
import UserAppointments from './pages/user/Appointments'
import UserPayment from './pages/user/Payment'
import UserToken from './pages/user/Token'
import UserHistory from './pages/user/History'
import UserProfile from './pages/user/Profile'

// Admin pages
import AdminLogin from './pages/admin/Login'
import AdminDashboard from './pages/admin/Dashboard'
import AdminUsers from './pages/admin/Users'
import AdminDoctors from './pages/admin/Doctors'
import AdminAppointments from './pages/admin/Appointments'
import AdminTokens from './pages/admin/Tokens'
import AdminPayments from './pages/admin/Payments'
import AdminConsultations from './pages/admin/Consultations'
import AdminMedicalRecords from './pages/admin/MedicalRecords'
import AdminReports from './pages/admin/Reports'
import AdminSettings from './pages/admin/Settings'

// Landing
import Landing from './pages/Landing'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />

        {/* User Portal */}
        <Route path="/user/login" element={<UserLogin />} />
        <Route path="/user/register" element={<UserRegister />} />
        <Route element={<ProtectedRoute role="patient" />}>
          <Route element={<UserLayout />}>
            <Route path="/user/dashboard" element={<UserDashboard />} />
            <Route path="/user/symptoms" element={<UserSymptoms />} />
            <Route path="/user/doctors" element={<UserDoctors />} />
            <Route path="/user/appointments" element={<UserAppointments />} />
            <Route path="/user/payment" element={<UserPayment />} />
            <Route path="/user/token" element={<UserToken />} />
            <Route path="/user/history" element={<UserHistory />} />
            <Route path="/user/profile" element={<UserProfile />} />
          </Route>
        </Route>

        {/* Admin Portal */}
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route element={<ProtectedRoute role="admin" />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
            <Route path="/admin/users" element={<AdminUsers />} />
            <Route path="/admin/doctors" element={<AdminDoctors />} />
            <Route path="/admin/appointments" element={<AdminAppointments />} />
            <Route path="/admin/tokens" element={<AdminTokens />} />
            <Route path="/admin/payments" element={<AdminPayments />} />
            <Route path="/admin/consultations" element={<AdminConsultations />} />
            <Route path="/admin/medical-records" element={<AdminMedicalRecords />} />
            <Route path="/admin/reports" element={<AdminReports />} />
            <Route path="/admin/settings" element={<AdminSettings />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
