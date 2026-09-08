import { NavLink } from 'react-router-dom'
import type { User } from '../types'

interface SidebarProps {
  user: User
  navItems: { to: string; label: string; icon: string }[]
  prefix?: string
}

export default function Sidebar({ user, navItems }: SidebarProps) {
  return (
    <div className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-primary-700">CareFlow AI</h1>
        <p className="text-xs text-gray-500 mt-1">{user.role === 'admin' ? 'Admin Portal' : 'Patient Portal'}</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-700 border border-primary-200'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`
            }
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-primary-700 font-bold text-sm">
            {user.full_name.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user.full_name}</p>
            <p className="text-xs text-gray-500 truncate">{user.email}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
