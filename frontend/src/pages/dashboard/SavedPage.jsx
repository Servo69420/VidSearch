import { SAMPLE_SAVED, ALL_VIDEOS } from '../../data/data'
import './SavedPage.css'

export default function SavedPage() {
  const saved = SAMPLE_SAVED.map(s => ({
    ...s,
    video: ALL_VIDEOS.find(v => v.id === s.videoId),
  })).filter(s => s.video)

  return (
    <div className="saved-page">
      <div className="saved-header">
        <h3>Saved Clips & Bookmarks</h3>
        <p>Your bookmarked video moments and notes.</p>
      </div>

      {saved.length === 0 ? (
        <div className="saved-empty">
          <div className="saved-empty-icon">&#128278;</div>
          <h4>No saved clips yet</h4>
          <p>Start watching videos and save key moments for later review.</p>
          <a href="#/watch" className="saved-empty-btn">Open Workspace</a>
        </div>
      ) : (
        <div className="saved-list">
          {saved.map(s => (
            <div key={s.id} className="saved-item">
              <div className={`saved-thumb ${s.video.color}`}>{s.video.icon}</div>
              <div className="saved-content">
                <div className="saved-video-title">{s.video.title}</div>
                <div className="saved-timestamp">&#9201; {s.timestamp}</div>
                <div className="saved-note">&ldquo;{s.note}&rdquo;</div>
                <div className="saved-time">{s.savedAt}</div>
              </div>
              <button className="saved-play-btn" onClick={() => window.location.hash = `#/watch/${s.videoId}`}>
                &#9654;
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
