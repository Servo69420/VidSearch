import { useState } from 'react'
import { SAMPLE_HISTORY } from '../../data/data'
import SearchBar from '../../components/ui/SearchBar'
import './HistoryPage.css'

export default function HistoryPage() {
  const [search, setSearch] = useState('')

  const filtered = search.trim()
    ? SAMPLE_HISTORY.filter(h =>
        h.query.toLowerCase().includes(search.toLowerCase()) ||
        h.videoTitle.toLowerCase().includes(search.toLowerCase())
      )
    : SAMPLE_HISTORY

  return (
    <div className="history-page">
      <div className="history-header">
        <div>
          <h3>Search History</h3>
          <p>Your past questions and searches.</p>
        </div>
        <button className="history-clear-btn">Clear History</button>
      </div>

      <SearchBar placeholder="Filter history..." value={search} onChange={setSearch} className="history-search" />

      {filtered.length === 0 ? (
        <div className="history-empty">
          <p>No matching history found.</p>
        </div>
      ) : (
        <div className="history-list">
          {filtered.map(h => (
            <div key={h.id} className="history-item">
              <div className="history-icon">&#128269;</div>
              <div className="history-content">
                <div className="history-query">{h.query}</div>
                <div className="history-meta">
                  <span className="history-video">{h.videoTitle}</span>
                  <span className="history-time">{h.timestamp}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
