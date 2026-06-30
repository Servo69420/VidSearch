import { createContext, useContext, useState, useCallback, useEffect } from 'react'

const HistoryContext = createContext()
const HISTORY_KEY = 'videoHistory_barebones'
const CHATTED_KEY = 'videoChatted_barebones'

export function HistoryProvider({ children }) {
  const [entries, setEntries] = useState([])

  useEffect(() => {
    try {
      setEntries(JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'))
    } catch { setEntries([]) }
  }, [])

  const [chattedIds, setChattedIds] = useState([])

  useEffect(() => {
    try {
      setChattedIds(JSON.parse(localStorage.getItem(CHATTED_KEY) || '[]'))
    } catch { setChattedIds([]) }
  }, [])

  const recordVisit = useCallback((id) => {
    const numId = typeof id === 'string' ? parseInt(id) : id
    if (!numId) return
    setEntries(prev => {
      const filtered = prev.filter(e => e.id !== numId)
      const next = [{ id: numId, visitedAt: new Date().toISOString() }, ...filtered].slice(0, 100)
      try { localStorage.setItem(HISTORY_KEY, JSON.stringify(next)) } catch {}
      return next
    })
  }, [])

  const recordChat = useCallback((videoId) => {
    if (!videoId) return
    setChattedIds(prev => {
      if (prev.includes(videoId)) return prev
      const next = [...prev, videoId]
      try { localStorage.setItem(CHATTED_KEY, JSON.stringify(next)) } catch {}
      return next
    })
  }, [])

  function recentIds(n = 5) {
    return entries.slice(0, n).map(e => e.id)
  }

  return (
    <HistoryContext.Provider value={{ recordVisit, recentIds, entries, recordChat, videosExplainedCount: chattedIds.length }}>
      {children}
    </HistoryContext.Provider>
  )
}

export function useHistory() {
  return useContext(HistoryContext)
}
