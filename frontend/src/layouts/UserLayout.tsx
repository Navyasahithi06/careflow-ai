import { Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'

const userNavItems = [
  { to: '/user/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/user/symptoms', label: 'Symptoms', icon: '🔍' },
  { to: '/user/doctors', label: 'Doctors', icon: '👨‍⚕️' },
  { to: '/user/appointments', label: 'Appointments', icon: '📅' },
  { to: '/user/payment', label: 'Payment', icon: '💳' },
  { to: '/user/token', label: 'Token', icon: '🎫' },
  { to: '/user/history', label: 'History', icon: '📝' },
  { to: '/user/profile', label: 'Profile', icon: '👤' },
]

export default function UserLayout() {
  const { user } = useAuth()
  if (!user) return null
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar user={user} navItems={userNavItems} prefix="/user" />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
