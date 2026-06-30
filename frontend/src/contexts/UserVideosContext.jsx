import { createContext, useContext, useState, useCallback, useEffect } from 'react'

const UserVideosContext = createContext()
const USER_VIDEOS_KEY = 'userVideos_barebones'

export function UserVideosProvider({ children }) {
  const [userVideos, setUserVideos] = useState([])

  useEffect(() => {
    try {
      setUserVideos(JSON.parse(localStorage.getItem(USER_VIDEOS_KEY) || '[]'))
    } catch { setUserVideos([]) }
  }, [])

  const addUserVideo = useCallback((video) => {
    setUserVideos(prev => {
      const filtered = prev.filter(v => v.id !== video.id)
      const next = [video, ...filtered].slice(0, 50)
      try { localStorage.setItem(USER_VIDEOS_KEY, JSON.stringify(next)) } catch {}
      return next
    })
  }, [])

  return (
    <UserVideosContext.Provider value={{ userVideos, addUserVideo }}>
      {children}
    </UserVideosContext.Provider>
  )
}

export function useUserVideos() {
  return useContext(UserVideosContext)
}
