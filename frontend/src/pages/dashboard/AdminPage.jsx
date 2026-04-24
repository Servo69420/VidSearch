import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { navigate } from '../../router'
import './AdminPage.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function StatCard({ icon, label, value, sub }) {
  return (
    <div className="adm-card">
      <div className="adm-card-icon">{icon}</div>
      <div className="adm-card-body">
        <div className="adm-card-value">{value ?? '—'}</div>
        <div className="adm-card-label">{label}</div>
        {sub && <div className="adm-card-sub">{sub}</div>}
      </div>
    </div>
  )
}

export default function AdminPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(null)

  useEffect(() => {
    if (user && !user.is_admin) {
      navigate('/dashboard')
      return
    }
    fetchStats()
  }, [user])

  async function fetchStats() {
    const token = localStorage.getItem('auth_token')
    try {
      const res = await fetch(`${API_BASE}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to load statistics.')
      setStats(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleExport(endpoint, fallbackName) {
    setExporting(endpoint)
    const token = localStorage.getItem('auth_token')
    try {
      const res = await fetch(`${API_BASE}/admin/${endpoint}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Export failed.')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const cd = res.headers.get('content-disposition') || ''
      const match = cd.match(/filename=(.+)/)
      a.download = match ? match[1] : fallbackName
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e.message)
    } finally {
      setExporting(null)
    }
  }

  if (loading) return <div className="adm-page"><p className="adm-loading">Loading statistics…</p></div>

  return (
    <div className="adm-page">
      <div className="adm-header">
        <div>
          <h2>Platform Statistics</h2>
          <p className="adm-subtitle">
            Admin view
            {stats && ` · ${new Date(stats.generated_at).toLocaleString()}`}
          </p>
        </div>
        <div className="adm-export-group">
          <button
            className="adm-export-btn"
            onClick={() => handleExport('stats/export.csv', 'vidsearch_stats.csv')}
            disabled={!!exporting || !stats}
          >
            {exporting === 'stats/export.csv' ? 'Exporting…' : 'Users CSV'}
          </button>
          <button
            className="adm-export-btn"
            onClick={() => handleExport('transcriptions/export.csv', 'vidsearch_transcriptions.csv')}
            disabled={!!exporting || !stats}
          >
            {exporting === 'transcriptions/export.csv' ? 'Exporting…' : 'Transcriptions CSV'}
          </button>
          <button
            className="adm-export-btn"
            onClick={() => handleExport('videos/export.csv', 'vidsearch_videos.csv')}
            disabled={!!exporting || !stats}
          >
            {exporting === 'videos/export.csv' ? 'Exporting…' : 'Videos CSV'}
          </button>
        </div>
      </div>

      {error && <p className="adm-error">{error}</p>}

      {stats && (
        <>
          <div className="adm-cards">
            <StatCard
              icon="&#128101;"
              label="Total Users"
              value={stats.users.total}
              sub={`+${stats.users.new_last_7_days} this week · +${stats.users.new_last_30_days} this month`}
            />
            <StatCard
              icon="&#128221;"
              label="Transcriptions"
              value={stats.transcriptions.total}
              sub={`${stats.transcriptions.youtube} YouTube · ${stats.transcriptions.uploaded} uploads`}
            />
            <StatCard
              icon="&#127916;"
              label="Total Videos"
              value={stats.videos.total}
              sub={`${stats.videos.youtube_videos} YouTube · ${stats.videos.user_uploaded} uploaded`}
            />
            <StatCard
              icon="&#128172;"
              label="Chat Messages"
              value={stats.chat.total_messages}
              sub={`${stats.chat.user_questions} questions · ${stats.chat.chat_sessions} sessions`}
            />
          </div>

          <div className="adm-grid">
            <div className="adm-section">
              <h4>Users by Subscription</h4>
              <table className="adm-table">
                <thead>
                  <tr><th>Plan</th><th>Users</th></tr>
                </thead>
                <tbody>
                  {stats.users.by_subscription.map(row => (
                    <tr key={row.subscription}>
                      <td>
                        <span className={`adm-badge adm-badge-${row.subscription}`}>
                          {row.subscription}
                        </span>
                      </td>
                      <td>{row.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="adm-section">
              <h4>Transcriptions by Status</h4>
              <table className="adm-table">
                <thead>
                  <tr><th>Status</th><th>Count</th></tr>
                </thead>
                <tbody>
                  {stats.transcriptions.by_status.map(row => (
                    <tr key={row.status}>
                      <td>
                        <span className={`adm-badge adm-badge-${row.status}`}>
                          {row.status}
                        </span>
                      </td>
                      <td>{row.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="adm-section adm-section-wide">
              <h4>Estimated Transcription Cost</h4>
              <div className="adm-cost">
                <div className="adm-cost-row">
                  <span>Estimated audio duration</span>
                  <strong>{stats.transcriptions.est_minutes} min</strong>
                </div>
                <div className="adm-cost-row">
                  <span>Whisper API cost <span className="adm-cost-rate">($0.006 / min)</span></span>
                  <strong>${stats.transcriptions.est_cost_usd}</strong>
                </div>
                <p className="adm-cost-note">
                  Duration is estimated from transcript word count (~130 words/min).
                  Actual charges depend on audio length.
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
