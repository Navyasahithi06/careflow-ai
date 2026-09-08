import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import NotificationBell from './NotificationBell'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">
          Welcome, {user?.full_name}
        </h2>
      </div>
      <div className="flex items-center gap-2">
        <NotificationBell />
        <button
          onClick={handleLogout}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Logout
        </button>
      </div>
    </header>
  )
}
