import { useState } from 'react'
import './ExplainPage.css'

// Extract YouTube video ID from common URL formats
function parseYouTubeId(url) {
  const patterns = [
    /(?:v=)([^&\n?#]+)/,
    /(?:youtu\.be\/)([^&\n?#]+)/,
    /(?:embed\/)([^&\n?#]+)/,
  ]
  for (const re of patterns) {
    const m = url.match(re)
    if (m) return m[1]
  }
  return null
}

const DEFAULT_VIDEO_ID = 'aircAruvnKk' // 3Blue1Brown — Neural Networks

const PLACEHOLDER_MESSAGES = [
  {
    role: 'assistant',
    text: 'Hi! Paste a YouTube link above and I\'ll help you understand the video. You can ask me anything about its content.',
  },
  {
    role: 'user',
    text: 'What is a neural network?',
  },
  {
    role: 'assistant',
    text: 'A neural network is a system of layers of interconnected nodes (neurons) loosely inspired by the human brain. Each layer transforms its input and passes it forward — the final layer produces a prediction or output.\n\nIn this video, 3Blue1Brown visualises how weights and biases shape those transformations.',
  },
]

export default function ExplainPage() {
  const [urlInput, setUrlInput]   = useState('')
  const [videoId, setVideoId]     = useState(DEFAULT_VIDEO_ID)
  const [urlError, setUrlError]   = useState(false)
  const [chatInput, setChatInput] = useState('')

  function handleLoadVideo() {
    const id = parseYouTubeId(urlInput.trim())
    if (id) {
      setVideoId(id)
      setUrlError(false)
    } else {
      setUrlError(true)
    }
  }

  function handleUrlKeyDown(e) {
    if (e.key === 'Enter') handleLoadVideo()
  }

  return (
    <div className="explain-layout">

      {/* ── Left panel — video ── */}
      <div className="explain-left">

        {/* URL bar */}
        <div className="url-bar">
          <span className="url-icon">▶</span>
          <input
            className={urlError ? 'url-input error' : 'url-input'}
            value={urlInput}
            onChange={e => { setUrlInput(e.target.value); setUrlError(false) }}
            onKeyDown={handleUrlKeyDown}
            placeholder="Paste a YouTube URL and press Enter…"
          />
          <button className="url-load-btn" onClick={handleLoadVideo}>
            Load
          </button>
        </div>
        {urlError && (
          <div className="url-error">Could not parse a YouTube video ID from that URL.</div>
        )}

        {/* Embed */}
        <div className="video-embed-wrapper">
          <iframe
            key={videoId}
            className="video-embed"
            src={`https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1`}
            title="YouTube video"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>

        {/* Video meta placeholder */}
        <div className="video-details">
          <div className="video-details-title">
            {videoId === DEFAULT_VIDEO_ID
              ? 'But what is a neural network? — 3Blue1Brown'
              : 'Video loaded'}
          </div>
          <div className="video-details-meta">
            <span className="placeholder-tag">⚠ Placeholder</span>
            <span>Title, description & transcript will be fetched by the backend</span>
          </div>

          <div className="segment-row">
            <div className="segment-label">Segments</div>
            <div className="segment-list">
              {['0:00 Introduction', '1:42 Neurons & layers', '4:10 Weights & biases', '7:30 Activation functions', '11:05 Training overview'].map((s, i) => (
                <button key={i} className={`segment-chip ${i === 1 ? 'segment-active' : ''}`}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Right panel — chat placeholder ── */}
      <div className="explain-right">
        <div className="chat-header">
          <div className="chat-header-left">
            <div className="chat-avatar">AI</div>
            <div>
              <div className="chat-name">VideoSearch Explainer</div>
              <div className="chat-status">
                <span className="status-dot" />
                LLM API — not connected yet
              </div>
            </div>
          </div>
          <span className="placeholder-tag">⚠ Placeholder</span>
        </div>

        <div className="chat-messages">
          {PLACEHOLDER_MESSAGES.map((msg, i) => (
            <div key={i} className={`chat-bubble-row ${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className="bubble-avatar">AI</div>
              )}
              <div className={`chat-bubble ${msg.role}`}>
                {msg.text.split('\n\n').map((para, j) => (
                  <p key={j}>{para}</p>
                ))}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          <div className="chat-bubble-row assistant">
            <div className="bubble-avatar">AI</div>
            <div className="chat-bubble assistant typing">
              <span /><span /><span />
            </div>
          </div>
        </div>

        <div className="chat-input-area">
          <div className="chat-input-notice">
            Chat will be powered by the LLM API — coming soon.
          </div>
          <div className="chat-input-row">
            <input
              className="chat-input"
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              placeholder="Ask about this video…"
              disabled
            />
            <button className="chat-send-btn" disabled>
              ↑
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
