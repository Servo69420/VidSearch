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

function handleHistoryItemClick(h) {
  if (h.yt_source_url) {
    const ytId = extractYouTubeId(h.yt_source_url)
    if (ytId) {
      sessionStorage.setItem('openUserVideo', JSON.stringify({
        type: 'youtube', youtubeId: ytId, title: h.video_title,
      }))
      navigate('/watch')
      return
    }
  }
  if (h.uv_file_path) {
    const parts = h.uv_file_path.replace(/\\/g, '/').split('/')
    const videosIdx = parts.lastIndexOf('videos')
    const relative = videosIdx >= 0 ? parts.slice(videosIdx).join('/') : parts[parts.length - 1]
    sessionStorage.setItem('openUserVideo', JSON.stringify({
      type: 'upload', localUrl: `http://localhost:8000/uploads/${relative}`, title: h.video_title,
    }))
    navigate('/watch')
  }
}

function formatVideoTitle(title) {
  if (!title) return 'Unknown Video'
  const ytMatch = title.match(/[?&]v=([^&]+)/)
  if (ytMatch) return `YouTube · ${ytMatch[1]}`
  return title
}

export default function HistoryPage() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [clearing, setClearing] = useState(false)

  const fetchHistory = useCallback(async () => {
    const token = localStorage.getItem('auth_token')
    if (!token) { setLoading(false); return }
    try {
      const res = await fetch(`${API_BASE}/chat-history/all`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to load history.')
      setHistory(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchHistory() }, [fetchHistory])

  async function handleClear() {
    if (!window.confirm('Clear all question history? This cannot be undone.')) return
    setClearing(true)
    const token = localStorage.getItem('auth_token')
    try {
      const res = await fetch(`${API_BASE}/chat-history/all`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error()
      setHistory([])
    } catch {
      setError('Failed to clear history.')
    } finally {
      setClearing(false)
    }
  }

  const filtered = search.trim()
    ? history.filter(h =>
        h.content.toLowerCase().includes(search.toLowerCase()) ||
        formatVideoTitle(h.video_title).toLowerCase().includes(search.toLowerCase())
      )
    : history

  return (
    <div className="history-page">
      <div className="history-header">
        <div>
          <h3>Question History</h3>
          <p>
            {loading
              ? 'Loading…'
              : `${history.length} question${history.length !== 1 ? 's' : ''} asked across all videos.`}
          </p>
        </div>
        {history.length > 0 && (
          <button className="history-clear-btn" onClick={handleClear} disabled={clearing}>
            {clearing ? 'Clearing…' : 'Clear History'}
          </button>
        )}
      </div>

      <SearchBar
        placeholder="Filter by question or video…"
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
              ? 'No matching questions found.'
              : 'No questions asked yet. Start chatting in the workspace!'}
          </p>
        </div>
      ) : (
        <div className="history-list">
          {filtered.map(h => (
            <div key={h.id} className="history-item" onClick={() => handleHistoryItemClick(h)}>
              <div className="history-icon">&#128172;</div>
              <div className="history-content">
                <div className="history-query">{h.content}</div>
                <div className="history-meta">
                  <span className="history-video">{formatVideoTitle(h.video_title)}</span>
                  <span className="history-dot">·</span>
                  <span className="history-time">{formatTime(h.created_at)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
