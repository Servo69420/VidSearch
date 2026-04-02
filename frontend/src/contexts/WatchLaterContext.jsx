import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { useAuth } from './AuthContext'

const WatchLaterContext = createContext()

export function WatchLaterProvider({ children }) {
  const { user } = useAuth()
  const key = user?.id ? `watchLater_${user.id}` : null

  const [entries, setEntries] = useState([])

  useEffect(() => {
    if (!key) { setEntries([]); return }
    try {
      setEntries(JSON.parse(localStorage.getItem(key) || '[]'))
    } catch { setEntries([]) }
  }, [key])

  const toggle = useCallback((id) => {
    if (!key) return
    setEntries(prev => {
      const exists = prev.some(e => e.id === id)
      const next = exists
        ? prev.filter(e => e.id !== id)
        : [...prev, { id, addedAt: new Date().toISOString() }]
      try { localStorage.setItem(key, JSON.stringify(next)) } catch {}
      return next
    })
  }, [key])

  const isFavourite = useCallback((id) => entries.some(e => e.id === id), [entries])

  const totalCount = entries.length

  const todayCount = entries.filter(e => {
    const d = new Date(e.addedAt)
    const now = new Date()
    return (
      d.getFullYear() === now.getFullYear() &&
      d.getMonth() === now.getMonth() &&
      d.getDate() === now.getDate()
    )
  }).length

  return (
    <WatchLaterContext.Provider value={{ toggle, isFavourite, totalCount, todayCount }}>
      {children}
    </WatchLaterContext.Provider>
  )
}

export function useWatchLater() {
  return useContext(WatchLaterContext)
}
