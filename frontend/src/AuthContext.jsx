import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const s = localStorage.getItem('vidsearch_user')
      return s ? JSON.parse(s) : null
    } catch { return null }
  })

  function register(userData) {
    localStorage.setItem('vidsearch_user', JSON.stringify(userData))
    setUser(userData)
  }

  function login(name) {
    try {
      const s = localStorage.getItem('vidsearch_user')
      if (s) {
        const stored = JSON.parse(s)
        if (stored.name.toLowerCase() === name.toLowerCase()) {
          setUser(stored)
          return true
        }
      }
    } catch {}
    return false
  }

  function logout() {
    localStorage.removeItem('vidsearch_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, register, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
