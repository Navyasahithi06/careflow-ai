import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import axios from 'axios'
import type { User, AuthResponse } from '../types'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string, role: 'patient' | 'admin') => Promise<void>
  register: (email: string, fullName: string, password: string, phone?: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('cf_token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      axios.get('/api/auth/me')
        .then(res => setUser(res.data))
        .catch(() => { localStorage.removeItem('cf_token'); setToken(null); })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token])

  const login = async (email: string, password: string, role: 'patient' | 'admin') => {
    const url = role === 'admin' ? '/api/auth/admin/login' : '/api/auth/login'
    const res = await axios.post<AuthResponse>(url, { email, password })
    localStorage.setItem('cf_token', res.data.access_token)
    setToken(res.data.access_token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${res.data.access_token}`
    const meRes = await axios.get('/api/auth/me')
    setUser(meRes.data)
  }

  const register = async (email: string, fullName: string, password: string, phone?: string) => {
    await axios.post('/api/auth/register', { email, full_name: fullName, password, phone })
  }

  const logout = () => {
    localStorage.removeItem('cf_token')
    setToken(null)
    setUser(null)
    delete axios.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
