import { useState, useMemo } from 'react'
import { ALL_VIDEOS, TOPICS } from '../../data/data'
import { useWatchLater } from '../../contexts/WatchLaterContext'
import { useUserVideos } from '../../contexts/UserVideosContext'
import VideoCard from '../../components/ui/VideoCard'
import SearchBar from '../../components/ui/SearchBar'
import './BrowseVideosPage.css'

export default function BrowseVideosPage() {
  const { toggle, isFavourite } = useWatchLater()
  const { userVideos } = useUserVideos()

  const [search, setSearch] = useState('')
  const [activeTopic, setActiveTopic] = useState(() => {
    if (sessionStorage.getItem('openFavourite')) {
      sessionStorage.removeItem('openFavourite')
      return 'Favourite'
    }
    if (sessionStorage.getItem('openMyVideos')) {
      sessionStorage.removeItem('openMyVideos')
      return 'My Videos'
    }
    const topic = sessionStorage.getItem('openTopic')
    if (topic) {
      sessionStorage.removeItem('openTopic')
      return topic
    }
    return 'All'
  })
  const [sort, setSort] = useState('title')

  const filtered = useMemo(() => {
    if (activeTopic === 'My Videos') {
      let vids = userVideos.map(v => ({
        id: v.id,
        title: v.title,
        subject: v.type === 'youtube' ? 'YouTube Video' : 'Uploaded File',
        color: v.type === 'youtube' ? 'thumb-sky' : 'thumb-teal',
        icon: '▶',
        duration: '',
        _isUserVideo: true,
        _userVideoData: v,
      }))
      if (search.trim()) {
        const q = search.toLowerCase()
        vids = vids.filter(v => v.title.toLowerCase().includes(q))
      }
      if (sort === 'title') vids.sort((a, b) => a.title.localeCompare(b.title))
      return vids
    }

    let vids = [...ALL_VIDEOS]

    if (activeTopic === 'Favourite') {
      vids = vids.filter(v => isFavourite(v.id))
    } else if (activeTopic !== 'All') {
      vids = vids.filter(v => v.subject === activeTopic)
    }

    if (search.trim()) {
      const q = search.toLowerCase()
      vids = vids.filter(v =>
        v.title.toLowerCase().includes(q) ||
        v.subject.toLowerCase().includes(q)
      )
    }

    if (sort === 'title') vids.sort((a, b) => a.title.localeCompare(b.title))
    if (sort === 'duration') vids.sort((a, b) => {
      const toSec = d => { const [m, s] = d.split(':').map(Number); return m * 60 + s }
      return toSec(a.duration) - toSec(b.duration)
    })
    if (sort === 'subject') vids.sort((a, b) => a.subject.localeCompare(b.subject))

    return vids
  }, [search, activeTopic, sort, isFavourite, userVideos])

  function handleVideoClick(v) {
    if (v._isUserVideo) {
      sessionStorage.setItem('openUserVideo', JSON.stringify(v._userVideoData))
      window.location.hash = '#/watch'
    } else {
      window.location.hash = `#/watch/${v.id}`
    }
  }

  return (
    <div className="browse-page">
      <div className="container">
        <div className="browse-header">
          <div>
            <h2>Browse Videos</h2>
            <p>Explore our library of educational videos across multiple subjects.</p>
          </div>
        </div>

        <div className="browse-controls">
          <SearchBar
            placeholder="Search videos by title or subject..."
            value={search}
            onChange={setSearch}
            className="browse-search"
          />
          <div className="browse-sort">
            <label>Sort by:</label>
            <select value={sort} onChange={e => setSort(e.target.value)}>
              <option value="title">Title</option>
              <option value="duration">Duration</option>
              <option value="subject">Subject</option>
            </select>
          </div>
        </div>

        <div className="browse-topics">
          <button
            className={`topic-btn ${activeTopic === 'All' ? 'active' : ''}`}
            onClick={() => setActiveTopic('All')}
          >
            All ({ALL_VIDEOS.length})
          </button>
          <button
            className={`topic-btn topic-btn-fav ${activeTopic === 'Favourite' ? 'active' : ''}`}
            onClick={() => setActiveTopic('Favourite')}
          >
            ♥ Favourites
          </button>
          <button
            className={`topic-btn topic-btn-mine ${activeTopic === 'My Videos' ? 'active' : ''}`}
            onClick={() => setActiveTopic('My Videos')}
          >
            ▶ My Videos ({userVideos.length})
          </button>
          {TOPICS.map(t => (
            <button
              key={t.label}
              className={`topic-btn ${activeTopic === t.label ? 'active' : ''}`}
              onClick={() => setActiveTopic(t.label)}
            >
              {t.label} ({t.count})
            </button>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className="browse-empty">
            <div className="browse-empty-icon">
              {activeTopic === 'Favourite' ? '♡' : activeTopic === 'My Videos' ? '▶' : '🔍'}
            </div>
            <h4>
              {activeTopic === 'Favourite'
                ? 'No favourites yet'
                : activeTopic === 'My Videos'
                ? 'No personal videos yet'
                : 'No videos found'}
            </h4>
            <p>
              {activeTopic === 'Favourite'
                ? 'Click the ♡ on any video to add it to your favourites.'
                : activeTopic === 'My Videos'
                ? 'Load a YouTube URL or upload a video file in the workspace to add your own videos.'
                : 'Try adjusting your search or filter criteria.'}
            </p>
          </div>
        ) : (
          <div className="browse-grid">
            {filtered.map(v => (
              <VideoCard
                key={v.id}
                video={v}
                onClick={() => handleVideoClick(v)}
                isFavourite={!v._isUserVideo && isFavourite(v.id)}
                onToggleFavourite={v._isUserVideo ? null : toggle}
              />
            ))}
          </div>
        )}

        <div className="browse-results-count">
          {activeTopic === 'Favourite'
            ? `${filtered.length} favourited video${filtered.length !== 1 ? 's' : ''}`
            : activeTopic === 'My Videos'
            ? `${filtered.length} personal video${filtered.length !== 1 ? 's' : ''}`
            : `Showing ${filtered.length} of ${ALL_VIDEOS.length} videos`}
        </div>
      </div>
    </div>
  )
}
