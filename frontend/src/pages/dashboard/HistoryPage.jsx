import { useState, useEffect, useCallback } from 'react'
import { navigate } from '../../router'
import SearchBar from '../../components/ui/SearchBar'
import './HistoryPage.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function formatTime(iso) {
  const date = new Date(iso)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}

function extractYouTubeId(url) {
  if (!url) return null
  const match = url.match(/[?&]v=([^&]+)/)
  return match ? match[1] : null
}

function formatVideoTitle(h) {
  if (h.yt_source_url) {
    const ytId = extractYouTubeId(h.yt_source_url)
    if (h.video_title?.includes('youtube.com') || h.video_title?.includes('youtu.be')) {
      return ytId ? `YouTube · ${ytId}` : 'YouTube Video'
    }
    return h.video_title || 'YouTube Video'
  }
  return h.uv_file_name || h.video_title || 'Uploaded Video'
}

function handleVideoClick(h) {
  if (h.yt_source_url) {
    const ytId = extractYouTubeId(h.yt_source_url)
    if (ytId) {
      sessionStorage.setItem('openUserVideo', JSON.stringify({
        type: 'youtube', youtubeId: ytId, title: formatVideoTitle(h),
      }))
    } else {
      sessionStorage.setItem('openUserVideo', JSON.stringify({
        type: 'chat_only', chatVideoId: h.video_id, title: formatVideoTitle(h),
      }))
    }
    navigate('/watch')
    return
  }
  if (h.video_url && h.user_video_id) {
    sessionStorage.setItem('openUserVideo', JSON.stringify({
      type: 'upload',
      localUrl: `${API_BASE}${h.video_url}`,
      title: formatVideoTitle(h),
      videoId: h.user_video_id,
    }))
    navigate('/watch')
  }
}

export default function HistoryPage() {
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [clearing, setClearing] = useState(false)

  const fetchVideos = useCallback(async () => {
    const token = localStorage.getItem('auth_token')
    if (!token) { setLoading(false); return }
    try {
      const res = await fetch(`${API_BASE}/chat-history/videos`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to load history.')
      setVideos(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchVideos() }, [fetchVideos])

  async function handleClear() {
    if (!window.confirm('Clear all chat history? This cannot be undone.')) return
    setClearing(true)
    const token = localStorage.getItem('auth_token')
    try {
      const res = await fetch(`${API_BASE}/chat-history/all`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error()
      setVideos([])
    } catch {
      setError('Failed to clear history.')
    } finally {
      setClearing(false)
    }
  }

  const filtered = search.trim()
    ? videos.filter(h => formatVideoTitle(h).toLowerCase().includes(search.toLowerCase()))
    : videos

  return (
    <div className="history-page">
      <div className="history-header">
        <div>
          <h3>Chat History</h3>
          <p>
            {loading
              ? 'Loading…'
              : `${videos.length} video${videos.length !== 1 ? 's' : ''} with chat history.`}
          </p>
        </div>
        {videos.length > 0 && (
          <button className="history-clear-btn" onClick={handleClear} disabled={clearing}>
            {clearing ? 'Clearing…' : 'Clear History'}
          </button>
        )}
      </div>

      <SearchBar
        placeholder="Filter by video title…"
        value={search}
        onChange={setSearch}
        className="history-search"
      />

      {loading ? (
        <div className="history-empty"><p>Loading your history…</p></div>
      ) : error ? (
        <div className="history-empty"><p className="history-error">{error}</p></div>
      ) : filtered.length === 0 ? (
        <div className="history-empty">
          <p>
            {search
              ? 'No matching videos found.'
              : 'No chat history yet. Start chatting in the workspace!'}
          </p>
        </div>
      ) : (
        <div className="history-list">
          {filtered.map((h, i) => {
            const ytId = extractYouTubeId(h.yt_source_url)
            const thumbnail = ytId
              ? `https://img.youtube.com/vi/${ytId}/mqdefault.jpg`
              : null
            return (
              <div key={h.user_video_id || h.video_id || i} className="history-item" onClick={() => handleVideoClick(h)}>
                <div className="history-icon">
                  {thumbnail
                    ? <img src={thumbnail} alt="" className="history-thumbnail" />
                    : <span>&#127916;</span>}
                </div>
                <div className="history-content">
                  <div className="history-query">{formatVideoTitle(h)}</div>
                  <div className="history-meta">
                    <span className="history-video">
                      {h.yt_source_url ? 'YouTube' : 'Uploaded video'}
                    </span>
                    <span className="history-dot">·</span>
                    <span className="history-video">
                      {h.message_count} question{h.message_count !== 1 ? 's' : ''}
                    </span>
                    <span className="history-dot">·</span>
                    <span className="history-time">{formatTime(h.last_message_at)}</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
