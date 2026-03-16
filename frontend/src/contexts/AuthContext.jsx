import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const s = localStorage.getItem('videosearch_user')
      return s ? JSON.parse(s) : null
    } catch { return null }
  })

  function register(userData) {
    const fullUser = {
      ...userData,
      subscription: userData.subscription || 'free',
      email: userData.email || '',
      joinedAt: new Date().toISOString(),
    }
    localStorage.setItem('videosearch_user', JSON.stringify(fullUser))
    setUser(fullUser)
  }

  function login(username, password) {
    try {
      const s = localStorage.getItem('videosearch_user')
      if (s) {
        const stored = JSON.parse(s)
        if (stored.username && stored.username.toLowerCase() === username.toLowerCase() && stored.password === password) {
          setUser(stored)
          return true
        }
      }
    } catch {}
    return false
  }

  function logout() {
    localStorage.removeItem('videosearch_user')
    setUser(null)
  }

  function updateProfile(fields) {
    if (!user) return
    const updated = { ...user, ...fields }
    localStorage.setItem('videosearch_user', JSON.stringify(updated))
    setUser(updated)
  }

  return (
    <AuthContext.Provider value={{ user, register, login, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
