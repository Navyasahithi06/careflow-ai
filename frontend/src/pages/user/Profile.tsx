import { useAuth } from '../../context/AuthContext'

export default function UserProfile() {
  const { user } = useAuth()
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
        <p className="text-gray-500 mt-1">Manage your account information</p>
      </div>
      <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-2xl">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center text-primary-700 font-bold text-2xl">
            {user?.full_name?.charAt(0)}
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{user?.full_name}</h2>
            <p className="text-gray-500">{user?.email}</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Role</p>
            <p className="font-medium text-gray-900 capitalize">{user?.role}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Phone</p>
            <p className="font-medium text-gray-900">{user?.phone || 'Not provided'}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Status</p>
            <p className="font-medium text-gray-900">{user?.is_active === 1 ? 'Active' : 'Inactive'}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Member Since</p>
            <p className="font-medium text-gray-900">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
