import { ALL_VIDEOS } from '../../data/data'
import { useAuth } from '../../contexts/AuthContext'
import VideoCard from '../../components/ui/VideoCard'
import './VideoDetailsPage.css'

export default function VideoDetailsPage({ params }) {
  const { user } = useAuth()
  const videoId = parseInt(params?.id)
  const video = ALL_VIDEOS.find(v => v.id === videoId)

  if (!video) {
    return (
      <div className="vd-page">
        <div className="container">
          <div className="vd-not-found">
            <h3>Video not found</h3>
            <p>The video you are looking for does not exist.</p>
            <a href="#/browse" className="vd-btn-primary">Browse Videos</a>
          </div>
        </div>
      </div>
    )
  }

  const related = ALL_VIDEOS
    .filter(v => v.subject === video.subject && v.id !== video.id)
    .slice(0, 3)

  function handleStartLearning() {
    if (user) {
      window.location.hash = `#/watch/${video.id}`
    } else {
      window.location.hash = '#/login'
    }
  }

  return (
    <div className="vd-page">
      <div className="container">
        <div className="vd-breadcrumb">
          <a href="#/browse">Browse Videos</a>
          <span className="vd-sep">/</span>
          <span>{video.subject}</span>
          <span className="vd-sep">/</span>
          <span className="vd-current">{video.title}</span>
        </div>

        <div className="vd-layout">
          <div className="vd-main">
            <div className={`vd-thumbnail ${video.color}`}>
              <span className="vd-thumb-icon">{video.icon}</span>
              <div className="vd-play-overlay">
                <div className="vd-play-btn">&#9654;</div>
              </div>
            </div>

            <div className="vd-info">
              <div className="vd-subject-badge">{video.subject}</div>
              <h2>{video.title}</h2>
              <div className="vd-meta">
                <span className="vd-duration">&#9201; {video.duration}</span>
                <span className="vd-dot">&#183;</span>
                <span>Educational</span>
              </div>
              <p className="vd-description">{video.description}</p>

              <div className="vd-actions">
                <button className="vd-btn-primary" onClick={handleStartLearning}>
                  &#9654; Start Learning
                </button>
                <button className="vd-btn-outline">&#9734; Save for Later</button>
              </div>
            </div>

            <div className="vd-features">
              <h5>What you will learn</h5>
              <div className="vd-features-list">
                <div className="vd-feature-item">&#10003; AI-powered Q&A about this video</div>
                <div className="vd-feature-item">&#10003; Smart timestamp navigation</div>
                <div className="vd-feature-item">&#10003; Save key moments and notes</div>
                <div className="vd-feature-item">&#10003; Track your understanding progress</div>
              </div>
            </div>
          </div>

          {related.length > 0 && (
            <div className="vd-sidebar">
              <h5>Related Videos</h5>
              <div className="vd-related-list">
                {related.map(v => (
                  <VideoCard
                    key={v.id}
                    video={v}
                    onClick={() => window.location.hash = `#/video/${v.id}`}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
