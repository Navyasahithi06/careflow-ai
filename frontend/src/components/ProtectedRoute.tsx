import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface Props {
  role: 'patient' | 'admin'
}

export default function ProtectedRoute({ role }: Props) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to={`/${role === 'admin' ? 'admin' : 'user'}/login`} replace />
  }

  if (user.role !== role) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
