import { useState } from 'react'
import { useAuth } from './AuthContext'
import { ALL_VIDEOS, HOBBY_COLORS, TOPICS } from './data'
import './MyVideosPage.css'

function sortByHobbies(videos, hobbies) {
  return [...videos].sort((a, b) => {
    const aMatch = hobbies.includes(a.subject) ? 1 : 0
    const bMatch = hobbies.includes(b.subject) ? 1 : 0
    return bMatch - aMatch
  })
}

export default function MyVideosPage({ onSignIn }) {
  const { user } = useAuth()
  const [filter, setFilter] = useState('all')

  const hobbies = user?.hobbies ?? []
  const sorted = sortByHobbies(ALL_VIDEOS, hobbies)
  const displayed = filter === 'all' ? sorted : sorted.filter(v => v.subject === filter)

  return (
    <div className="myvideos-page">
      <div className="myvideos-header">
        {user ? (
          <>
            <h2>Recommended for {user.name}</h2>
            <p>Videos sorted by your interests · {displayed.length} videos</p>
          </>
        ) : (
          <>
            <h2>All Videos</h2>
            <p>
              <button className="link-btn-inline" onClick={onSignIn}>Sign in</button>
              {' '}to get personalised recommendations based on your interests.
            </p>
          </>
        )}

        <div className="filter-row">
          <button
            className={`topic-chip chip-neutral ${filter === 'all' ? 'chip-selected' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          {(hobbies.length > 0 ? hobbies : TOPICS.map(t => t.label)).map(h => (
            <button
              key={h}
              className={`topic-chip ${HOBBY_COLORS[h]?.chip ?? 'chip-indigo'} ${filter === h ? 'chip-selected' : ''}`}
              onClick={() => setFilter(filter === h ? 'all' : h)}
            >
              {h}
            </button>
          ))}
        </div>
      </div>

      <div className="myvideos-grid">
        {displayed.map(v => {
          const isRecommended = hobbies.includes(v.subject)
          return (
            <div className={`video-card ${isRecommended ? 'video-card-recommended' : ''}`} key={v.id}>
              <div className={`video-card-thumb ${v.color}`}>{v.icon}</div>
              <div className="video-card-body">
                <div className="video-card-title">{v.title}</div>
                <div className="video-card-meta">
                  <span className={`topic-chip ${HOBBY_COLORS[v.subject]?.chip ?? 'chip-indigo'} chip-sm`}>
                    {v.subject}
                  </span>
                  <span className="video-duration">{v.duration}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
