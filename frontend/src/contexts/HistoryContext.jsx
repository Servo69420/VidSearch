import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { useAuth } from './AuthContext'

const HistoryContext = createContext()

export function HistoryProvider({ children }) {
  const { user } = useAuth()
  const key = user?.id ? `videoHistory_${user.id}` : null

  const [entries, setEntries] = useState([])

  useEffect(() => {
    if (!key) { setEntries([]); return }
    try {
      setEntries(JSON.parse(localStorage.getItem(key) || '[]'))
    } catch { setEntries([]) }
  }, [key])

  const recordVisit = useCallback((id) => {
    if (!key) return
    const numId = typeof id === 'string' ? parseInt(id) : id
    if (!numId) return
    setEntries(prev => {
      const filtered = prev.filter(e => e.id !== numId)
      const next = [{ id: numId, visitedAt: new Date().toISOString() }, ...filtered].slice(0, 100)
      try { localStorage.setItem(key, JSON.stringify(next)) } catch {}
      return next
    })
  }, [key])

  function recentIds(n = 5) {
    return entries.slice(0, n).map(e => e.id)
  }

  return (
    <HistoryContext.Provider value={{ recordVisit, recentIds, entries }}>
      {children}
    </HistoryContext.Provider>
  )
}

export function useHistory() {
  return useContext(HistoryContext)
}
