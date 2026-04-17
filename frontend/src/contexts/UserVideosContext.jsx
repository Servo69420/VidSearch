import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { useAuth } from './AuthContext'

const UserVideosContext = createContext()

export function UserVideosProvider({ children }) {
  const { user } = useAuth()
  const key = user?.id ? `userVideos_${user.id}` : 'userVideos_guest'

  const [userVideos, setUserVideos] = useState([])

  useEffect(() => {
    try {
      setUserVideos(JSON.parse(localStorage.getItem(key) || '[]'))
    } catch { setUserVideos([]) }
  }, [key])

  const addUserVideo = useCallback((video) => {
    setUserVideos(prev => {
      const filtered = prev.filter(v => v.id !== video.id)
      const next = [video, ...filtered].slice(0, 50)
      try { localStorage.setItem(key, JSON.stringify(next)) } catch {}
      return next
    })
  }, [key])

  return (
    <UserVideosContext.Provider value={{ userVideos, addUserVideo }}>
      {children}
    </UserVideosContext.Provider>
  )
}

export function useUserVideos() {
  return useContext(UserVideosContext)
}
