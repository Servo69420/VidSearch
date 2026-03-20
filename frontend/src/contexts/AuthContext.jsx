import { createContext, useContext, useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (!token) { setLoading(false); return }
    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setUser(data) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // eslint-disable-next-line no-unused-vars
  async function register({ username, password, email, name: _name, surname: _surname, hobbies: _hobbies }) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email: email || null, password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Registration failed.')
    }
    await login(username, password)
  }

  async function login(username, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Invalid username or password.')
    }
    const { access_token } = await res.json()
    localStorage.setItem('auth_token', access_token)
    const meRes = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${access_token}` },
    })
    const userData = await meRes.json()
    setUser(userData)
  }

  function logout() {
    localStorage.removeItem('auth_token')
    setUser(null)
  }

  function updateProfile(fields) {
    if (!user) return
    setUser(prev => ({ ...prev, ...fields }))
  }

  return (
    <AuthContext.Provider value={{ user, loading, register, login, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
