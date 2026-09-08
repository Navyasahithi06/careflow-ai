import { Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'

const adminNavItems = [
  { to: '/admin/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/admin/users', label: 'Users', icon: '👥' },
  { to: '/admin/doctors', label: 'Doctors', icon: '👨‍⚕️' },
  { to: '/admin/appointments', label: 'Appointments', icon: '📅' },
  { to: '/admin/tokens', label: 'Tokens', icon: '🎫' },
  { to: '/admin/payments', label: 'Payments', icon: '💳' },
  { to: '/admin/consultations', label: 'Consultations', icon: '💬' },
  { to: '/admin/medical-records', label: 'Medical Records', icon: '📁' },
  { to: '/admin/reports', label: 'Reports', icon: '📈' },
  { to: '/admin/settings', label: 'Settings', icon: '⚙️' },
]

export default function AdminLayout() {
  const { user } = useAuth()
  if (!user) return null
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar user={user} navItems={adminNavItems} prefix="/admin" />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
