import { useState } from 'react'
import './App.css'
import ExplainPage from './ExplainPage'
import MyVideosPage from './MyVideosPage'
import AuthModal from './AuthModal'
import { useAuth } from './AuthContext'
import { ALL_VIDEOS, TOPICS, HOBBY_COLORS } from './data'

const NAV = [
  { icon: '⊞', label: 'Dashboard', id: 'dashboard' },
  { icon: '▶', label: 'My Videos',  id: 'videos' },
  { icon: '◎', label: 'Explain',    id: 'explain' },
  { icon: '★', label: 'Saved',      id: 'saved' },
]

const NAV_SECONDARY = [
  { icon: '⚙', label: 'Settings', id: 'settings' },
  { icon: '?', label: 'Help',      id: 'help' },
]

const PAGE_TITLES = {
  dashboard: 'Dashboard',
  videos:    'My Videos',
  explain:   'Explain',
  saved:     'Saved',
  settings:  'Settings',
  help:      'Help',
}

function sortByHobbies(videos, hobbies) {
  return [...videos].sort((a, b) => {
    const aMatch = hobbies.includes(a.subject) ? 1 : 0
    const bMatch = hobbies.includes(b.subject) ? 1 : 0
    return bMatch - aMatch
  })
}

export default function App() {
  const [activeNav, setActiveNav] = useState('dashboard')
  const [modalOpen, setModalOpen] = useState(false)
  const { user } = useAuth()

  const recommended = user
    ? sortByHobbies(ALL_VIDEOS, user.hobbies).slice(0, 5)
    : []

  const initials = user
    ? `${user.name[0]}${user.surname[0]}`.toUpperCase()
    : '?'

  return (
    <div className="layout">
      {modalOpen && <AuthModal onClose={() => setModalOpen(false)} />}

      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">▶</div>
          VidSearch
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">Menu</div>
          {NAV.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activeNav === item.id ? 'active' : ''}`}
              onClick={() => setActiveNav(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </button>
          ))}
        </div>

        <hr className="sidebar-divider" />

        <div className="sidebar-section">
          {NAV_SECONDARY.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activeNav === item.id ? 'active' : ''}`}
              onClick={() => setActiveNav(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="user-chip" onClick={() => setModalOpen(true)}>
            <div className="avatar" style={!user ? { background: 'var(--border)', color: 'var(--text-muted)' } : {}}>
              {initials}
            </div>
            <div className="user-info">
              {user ? (
                <>
                  <div className="user-name">{user.name} {user.surname}</div>
                  <div className="user-plan">
                    {user.hobbies.length} interest{user.hobbies.length !== 1 ? 's' : ''}
                  </div>
                </>
              ) : (
                <>
                  <div className="user-name">Sign in</div>
                  <div className="user-plan">Create an account</div>
                </>
              )}
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="main">
        {/* Topbar */}
        <header className="topbar">
          <span className="topbar-title">{PAGE_TITLES[activeNav] ?? 'VidSearch'}</span>
          <div className="search-bar">
            <span className="search-icon">⌕</span>
            <input placeholder="Search videos, topics, explanations…" />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost">+ Add video</button>
            <button className="btn btn-primary" onClick={() => setActiveNav('explain')}>▶ Explain</button>
          </div>
        </header>

        {/* Page */}
        <main className={activeNav === 'explain' ? 'page page-fullbleed' : 'page'}>
          {activeNav === 'explain' && <ExplainPage />}
          {activeNav === 'videos'  && <MyVideosPage onSignIn={() => setModalOpen(true)} />}
          {activeNav !== 'explain' && activeNav !== 'videos' && <>
            {/* Placeholder notice */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <span className="placeholder-tag">⚠ Placeholder</span>
              <span style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                All data below is static — real content connects via the FastAPI backend.
              </span>
            </div>

            {/* Welcome */}
            <div className="welcome-banner">
              <h2>Welcome back{user ? `, ${user.name}` : ''}!</h2>
              <p>
                {user
                  ? `Recommendations are sorted based on your ${user.hobbies.length} selected interest${user.hobbies.length !== 1 ? 's' : ''}.`
                  : 'Sign in to get personalised video recommendations.'}
              </p>
            </div>

            {/* Stats */}
            <div className="stats-row">
              <div className="stat-card">
                <div className="stat-label">Videos Explained</div>
                <div className="stat-value">24</div>
                <div className="stat-sub">↑ 4 this week</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Topics Covered</div>
                <div className="stat-value">6</div>
                <div className="stat-sub">↑ 1 new topic</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Watch Later</div>
                <div className="stat-value">11</div>
                <div className="stat-sub" style={{ color: 'var(--warning)' }}>3 added today</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Streak</div>
                <div className="stat-value">7 days</div>
                <div className="stat-sub">Personal best!</div>
              </div>
            </div>

            {/* Two-column grid */}
            <div className="grid-2">
              {/* Recent videos */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">Recent Videos</span>
                  <button className="card-action" onClick={() => setActiveNav('videos')}>View all</button>
                </div>
                <div className="card-body">
                  <div className="video-list">
                    {ALL_VIDEOS.slice(0, 5).map(v => (
                      <div className="video-item" key={v.id}>
                        <div className={`video-thumb ${v.color}`}>{v.icon}</div>
                        <div className="video-meta">
                          <div className="video-title">{v.title}</div>
                          <div className="video-info">{v.subject}</div>
                        </div>
                        <div className="video-duration">{v.duration}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Topics + Recommended stacked */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div className="card">
                  <div className="card-header">
                    <span className="card-title">My Topics</span>
                    <button className="card-action">Manage</button>
                  </div>
                  <div className="card-body">
                    <div className="topic-list">
                      {TOPICS.map((t, i) => (
                        <div className={`topic-chip ${t.color}`} key={i}>
                          {t.label}
                          <span className="topic-count">({t.count})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Recommended for You (replaces Recent Activity) */}
                <div className="card">
                  <div className="card-header">
                    <span className="card-title">Recommended for You</span>
                    {user && (
                      <button className="card-action" onClick={() => setActiveNav('videos')}>View all</button>
                    )}
                  </div>
                  <div className="card-body">
                    {!user ? (
                      <div className="rec-empty">
                        <p>Sign in to get personalised video recommendations based on your interests.</p>
                        <button
                          className="btn btn-primary"
                          style={{ marginTop: 12, fontSize: 13 }}
                          onClick={() => setModalOpen(true)}
                        >
                          Sign In
                        </button>
                      </div>
                    ) : (
                      <div className="video-list">
                        {recommended.map(v => (
                          <div className="video-item" key={v.id}>
                            <div className={`video-thumb ${v.color}`}>{v.icon}</div>
                            <div className="video-meta">
                              <div className="video-title">{v.title}</div>
                              <div className="video-info">{v.subject}</div>
                            </div>
                            <div className="video-duration">{v.duration}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>}
        </main>
      </div>
    </div>
  )
}
