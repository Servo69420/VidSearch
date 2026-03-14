import { useState, useMemo } from 'react'
import { ALL_VIDEOS, TOPICS } from '../../data/data'
import VideoCard from '../../components/ui/VideoCard'
import SearchBar from '../../components/ui/SearchBar'
import './BrowseVideosPage.css'

export default function BrowseVideosPage() {
  const [search, setSearch] = useState('')
  const [activeTopic, setActiveTopic] = useState('All')
  const [sort, setSort] = useState('title')

  const filtered = useMemo(() => {
    let vids = [...ALL_VIDEOS]

    if (activeTopic !== 'All') {
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
  }, [search, activeTopic, sort])

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
            <div className="browse-empty-icon">&#128269;</div>
            <h4>No videos found</h4>
            <p>Try adjusting your search or filter criteria.</p>
          </div>
        ) : (
          <div className="browse-grid">
            {filtered.map(v => (
              <VideoCard
                key={v.id}
                video={v}
                onClick={() => window.location.hash = `#/video/${v.id}`}
              />
            ))}
          </div>
        )}

        <div className="browse-results-count">
          Showing {filtered.length} of {ALL_VIDEOS.length} videos
        </div>
      </div>
    </div>
  )
}
