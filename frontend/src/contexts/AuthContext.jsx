import { createContext, useContext, useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const AuthContext = createContext(null)

function authHeaders() {
  const token = localStorage.getItem('auth_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  async function fetchMe(token) {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) {
      localStorage.removeItem('auth_token')
      return null
    }
    return res.json()
  }

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (!token) { setLoading(false); return }
    fetchMe(token)
      .then(data => { if (data) setUser(data) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  async function register({ username, password, email }) {
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
    const userData = await fetchMe(access_token)
    if (userData) setUser(userData)
  }

  function logout() {
    localStorage.removeItem('auth_token')
    setUser(null)
  }

  async function updateProfile(fields) {
    const res = await fetch(`${API_BASE}/auth/profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(fields),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Failed to update profile.')
    }
    setUser(prev => ({ ...prev, ...fields }))
  }

  async function uploadAvatar(file) {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API_BASE}/auth/avatar`, {
      method: 'POST',
      headers: authHeaders(),
      body: form,
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Failed to upload avatar.')
    }
    const { avatar_url } = await res.json()
    setUser(prev => ({ ...prev, avatar_url }))
    return avatar_url
  }

  return (
    <AuthContext.Provider value={{ user, loading, register, login, logout, updateProfile, uploadAvatar, API_BASE }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
