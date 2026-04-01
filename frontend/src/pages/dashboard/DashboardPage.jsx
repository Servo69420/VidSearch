import { useAuth } from '../../contexts/AuthContext'
import { useWatchLater } from '../../contexts/WatchLaterContext'
import { useHistory } from '../../contexts/HistoryContext'
import { ALL_VIDEOS, TOPICS, SAMPLE_USER_STATS } from '../../data/data'
import StatCard from '../../components/ui/StatCard'
import { navigate } from '../../router'
import './DashboardPage.css'

export default function DashboardPage() {
  const { user } = useAuth()
  const { totalCount, todayCount, isFavourite } = useWatchLater()
  const { recentIds, videosExplainedCount } = useHistory()
  const stats = SAMPLE_USER_STATS

  function openFavourites() {
    sessionStorage.setItem('openFavourite', '1')
    navigate('/browse')
  }

  function openTopic(label) {
    sessionStorage.setItem('openTopic', label)
    navigate('/browse')
  }

  const recentVideos = recentIds(5)
    .map(id => ALL_VIDEOS.find(v => v.id === id))
    .filter(Boolean)

  const recommended = user?.hobbies?.length
    ? ALL_VIDEOS.filter(v => user.hobbies.includes(v.subject)).slice(0, 10)
    : []

  return (
    <div className="dash">
      {/* Welcome */}
      <div className="dash-welcome">
        <div className="dash-welcome-content">
          <h2>Welcome back{user ? `, ${user.username}` : ''}!</h2>
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
        <StatCard label="Videos Explained" value={videosExplainedCount} change={videosExplainedCount > 0 ? `${videosExplainedCount} total` : 'None yet'} changeType={videosExplainedCount > 0 ? 'positive' : 'neutral'} icon="&#9654;" />
        <StatCard label="Topics Covered" value={stats.topicsCovered} change="+1 new topic" changeType="positive" icon="&#9733;" />
        <div onClick={openFavourites} style={{ cursor: 'pointer' }}>
          <StatCard
            label="Watch Later"
            value={totalCount}
            change={todayCount > 0 ? `+${todayCount} added today` : 'None added today'}
            changeType="neutral"
            icon="&#9201;"
          />
        </div>
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
            {recentVideos.length === 0 ? (
              <p className="dash-empty">No videos watched yet. <a href="#/browse">Browse videos</a></p>
            ) : (
              <div className="dash-video-list">
                {recentVideos.map(v => (
                  <a key={v.id} href={`#/watch/${v.id}`} className="dash-video-item">
                    <div className={`dash-video-thumb ${v.color}`}>{v.icon}</div>
                    <div className="dash-video-meta">
                      <div className="dash-video-title">{v.title}</div>
                      <div className="dash-video-info">{v.subject}</div>
                    </div>
                    <div className="dash-video-duration">{v.duration}</div>
                    {isFavourite(v.id) && <span className="dash-video-fav">♥</span>}
                  </a>
                ))}
              </div>
            )}
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
                  <button
                    key={i}
                    className={`dash-topic-chip ${t.color}`}
                    onClick={() => openTopic(t.label)}
                  >
                    {t.label}
                    <span className="dash-topic-count">({t.count})</span>
                  </button>
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
              {recommended.length === 0 ? (
                <p className="dash-empty">Select interests during sign-up to get recommendations. <a href="#/browse">Browse all videos</a></p>
              ) : (
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
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
