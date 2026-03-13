import { useAuth } from '../../contexts/AuthContext'
import { ALL_VIDEOS, TOPICS, SAMPLE_USER_STATS } from '../../data/data'
import StatCard from '../../components/ui/StatCard'
import './DashboardPage.css'

function sortByHobbies(videos, hobbies) {
  return [...videos].sort((a, b) => {
    const aMatch = hobbies.includes(a.subject) ? 1 : 0
    const bMatch = hobbies.includes(b.subject) ? 1 : 0
    return bMatch - aMatch
  })
}

export default function DashboardPage() {
  const { user } = useAuth()
  const stats = SAMPLE_USER_STATS

  const recommended = user?.hobbies
    ? sortByHobbies(ALL_VIDEOS, user.hobbies).slice(0, 5)
    : ALL_VIDEOS.slice(0, 5)

  return (
    <div className="dash">
      {/* Welcome */}
      <div className="dash-welcome">
        <div className="dash-welcome-content">
          <h2>Welcome back{user ? `, ${user.name}` : ''}!</h2>
          <p>
            {user?.hobbies?.length
              ? `Your recommendations are based on your ${user.hobbies.length} selected interest${user.hobbies.length !== 1 ? 's' : ''}.`
              : 'Start exploring videos and build your learning streak.'}
          </p>
          <a href="#/watch" className="dash-welcome-btn">&#9654; Open Workspace</a>
        </div>
        <div className="dash-welcome-deco">&#9654;</div>
      </div>

      {/* Stats */}
      <div className="dash-stats">
        <StatCard label="Videos Explained" value={stats.videosExplained} change="+4 this week" changeType="positive" icon="&#9654;" />
        <StatCard label="Topics Covered" value={stats.topicsCovered} change="+1 new topic" changeType="positive" icon="&#9733;" />
        <StatCard label="Watch Later" value={stats.watchLater} change="3 added today" changeType="neutral" icon="&#9201;" />
        <StatCard label="Learning Streak" value={`${stats.streak} days`} change="Personal best!" changeType="positive" icon="&#128293;" />
      </div>

      {/* Two-column grid */}
      <div className="dash-grid">
        {/* Recent Videos */}
        <div className="dash-card">
          <div className="dash-card-header">
            <span className="dash-card-title">Recent Videos</span>
            <a href="#/watched" className="dash-card-action">View all</a>
          </div>
          <div className="dash-card-body">
            <div className="dash-video-list">
              {ALL_VIDEOS.slice(0, 5).map(v => (
                <a
                  key={v.id}
                  href={`#/watch/${v.id}`}
                  className="dash-video-item"
                >
                  <div className={`dash-video-thumb ${v.color}`}>{v.icon}</div>
                  <div className="dash-video-meta">
                    <div className="dash-video-title">{v.title}</div>
                    <div className="dash-video-info">{v.subject}</div>
                  </div>
                  <div className="dash-video-duration">{v.duration}</div>
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Topics + Recommended */}
        <div className="dash-right-stack">
          <div className="dash-card">
            <div className="dash-card-header">
              <span className="dash-card-title">My Topics</span>
              <a href="#/browse" className="dash-card-action">Browse all</a>
            </div>
            <div className="dash-card-body">
              <div className="dash-topic-list">
                {TOPICS.map((t, i) => (
                  <a href="#/browse" className={`dash-topic-chip ${t.color}`} key={i}>
                    {t.label}
                    <span className="dash-topic-count">({t.count})</span>
                  </a>
                ))}
              </div>
            </div>
          </div>

          <div className="dash-card">
            <div className="dash-card-header">
              <span className="dash-card-title">Recommended</span>
              <a href="#/browse" className="dash-card-action">View all</a>
            </div>
            <div className="dash-card-body">
              <div className="dash-video-list">
                {recommended.map(v => (
                  <a
                    key={v.id}
                    href={`#/watch/${v.id}`}
                    className="dash-video-item"
                  >
                    <div className={`dash-video-thumb ${v.color}`}>{v.icon}</div>
                    <div className="dash-video-meta">
                      <div className="dash-video-title">{v.title}</div>
                      <div className="dash-video-info">{v.subject}</div>
                    </div>
                    <div className="dash-video-duration">{v.duration}</div>
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
