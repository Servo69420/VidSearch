import { ALL_VIDEOS } from '../../data/data'
import { useHistory } from '../../contexts/HistoryContext'
import { useWatchLater } from '../../contexts/WatchLaterContext'
import VideoCard from '../../components/ui/VideoCard'
import './WatchedPage.css'

function groupLabel(isoDate) {
  const d = new Date(isoDate)
  const now = new Date()
  const diffMs = now - d
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays <= 7) return 'This Week'
  return 'Earlier'
}

export default function WatchedPage() {
  const { entries } = useHistory()
  const { isFavourite, toggle } = useWatchLater()

  const watchedVideos = entries
    .map(e => ({ ...e, video: ALL_VIDEOS.find(v => v.id === e.id) }))
    .filter(e => e.video)

  const groupOrder = ['Today', 'Yesterday', 'This Week', 'Earlier']
  const grouped = groupOrder.reduce((acc, label) => ({ ...acc, [label]: [] }), {})
  watchedVideos.forEach(e => {
    const label = groupLabel(e.visitedAt)
    grouped[label].push(e)
  })

  const groups = groupOrder
    .filter(label => grouped[label].length > 0)
    .map(label => ({ label, items: grouped[label] }))

  return (
    <div className="watched-page">
      <div className="watched-header">
        <h3>Watched Videos</h3>
        <p>Videos you have previously watched.</p>
      </div>

      {groups.length === 0 && (
        <p className="watched-empty">No videos watched yet. <a href="#/browse">Browse videos</a></p>
      )}

      {groups.map(g => (
        <div key={g.label} className="watched-group">
          <h5 className="watched-group-label">{g.label}</h5>
          <div className="watched-grid">
            {g.items.map(e => (
              <VideoCard
                key={e.id}
                video={e.video}
                onClick={() => { window.location.hash = `#/watch/${e.video.id}` }}
                isFavourite={isFavourite(e.video.id)}
                onToggleFavourite={toggle}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
