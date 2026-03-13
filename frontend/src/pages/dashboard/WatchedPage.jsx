import { ALL_VIDEOS, SAMPLE_WATCHED } from '../../data/data'
import VideoCard from '../../components/ui/VideoCard'
import './WatchedPage.css'

export default function WatchedPage() {
  const watchedVideos = SAMPLE_WATCHED.map(w => ({
    ...w,
    video: ALL_VIDEOS.find(v => v.id === w.videoId),
  })).filter(w => w.video)

  const groups = [
    { label: 'Today', items: watchedVideos.filter(w => w.watchedAt.includes('hour')) },
    { label: 'This Week', items: watchedVideos.filter(w => w.watchedAt === 'Yesterday' || w.watchedAt.includes('days')) },
    { label: 'Earlier', items: watchedVideos.filter(w => w.watchedAt.includes('week')) },
  ].filter(g => g.items.length > 0)

  return (
    <div className="watched-page">
      <div className="watched-header">
        <h3>Watched Videos</h3>
        <p>Videos you have previously watched.</p>
      </div>

      {groups.map(g => (
        <div key={g.label} className="watched-group">
          <h5 className="watched-group-label">{g.label}</h5>
          <div className="watched-grid">
            {g.items.map(w => (
              <div key={w.videoId} className="watched-card-wrapper">
                <VideoCard
                  video={w.video}
                  onClick={() => window.location.hash = `#/watch/${w.video.id}`}
                />
                <div className="watched-progress">
                  <div className="watched-progress-bar" style={{ width: `${w.progress}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
