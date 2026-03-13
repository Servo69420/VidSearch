import { useState } from 'react'
import { ALL_VIDEOS } from '../../data/data'
import './WatchPage.css'

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

const PLACEHOLDER_MESSAGES = [
  { role: 'assistant', text: 'Hi! Paste a YouTube link above and I\'ll help you understand the video. You can ask me anything about its content.' },
  { role: 'user', text: 'What is a neural network?' },
  { role: 'assistant', text: 'A neural network is a system of layers of interconnected nodes (neurons) loosely inspired by the human brain. Each layer transforms its input and passes it forward \u2014 the final layer produces a prediction or output.\n\nIn this video, 3Blue1Brown visualises how weights and biases shape those transformations.' },
]

export default function WatchPage({ params }) {
  const videoFromParams = params?.id ? ALL_VIDEOS.find(v => v.id === parseInt(params.id)) : null
  const defaultYoutubeId = videoFromParams?.youtubeId || 'aircAruvnKk'
  const defaultTitle = videoFromParams?.title || 'But what is a neural network? \u2014 3Blue1Brown'

  const [urlInput, setUrlInput] = useState('')
  const [videoId, setVideoId] = useState(defaultYoutubeId)
  const [videoTitle, setVideoTitle] = useState(defaultTitle)
  const [urlError, setUrlError] = useState(false)
  const [chatInput, setChatInput] = useState('')

  function handleLoadVideo() {
    const id = parseYouTubeId(urlInput.trim())
    if (id) {
      setVideoId(id)
      setVideoTitle('Video loaded')
      setUrlError(false)
    } else {
      setUrlError(true)
    }
  }

  function handleUrlKeyDown(e) {
    if (e.key === 'Enter') handleLoadVideo()
  }

  return (
    <div className="watch-layout">
      {/* Left panel - video */}
      <div className="watch-left">
        <div className="watch-url-bar">
          <span className="watch-url-icon">&#9654;</span>
          <input
            className={`watch-url-input ${urlError ? 'error' : ''}`}
            value={urlInput}
            onChange={e => { setUrlInput(e.target.value); setUrlError(false) }}
            onKeyDown={handleUrlKeyDown}
            placeholder="Paste a YouTube URL and press Enter\u2026"
          />
          <button className="watch-url-btn" onClick={handleLoadVideo}>Load</button>
        </div>
        {urlError && <div className="watch-url-error">Could not parse a YouTube video ID from that URL.</div>}

        <div className="watch-embed-wrapper">
          <iframe
            key={videoId}
            className="watch-embed"
            src={`https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1`}
            title="YouTube video"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>

        <div className="watch-details">
          <div className="watch-title">{videoTitle}</div>
          <div className="watch-segments">
            <div className="watch-seg-label">Segments</div>
            <div className="watch-seg-list">
              {['0:00 Introduction', '1:42 Neurons & layers', '4:10 Weights & biases', '7:30 Activation functions', '11:05 Training overview'].map((s, i) => (
                <button key={i} className={`watch-seg-chip ${i === 1 ? 'active' : ''}`}>{s}</button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right panel - chat */}
      <div className="watch-right">
        <div className="watch-chat-header">
          <div className="watch-chat-header-left">
            <div className="watch-chat-avatar">AI</div>
            <div>
              <div className="watch-chat-name">VideoSearch Explainer</div>
              <div className="watch-chat-status">
                <span className="watch-status-dot" />
                AI Assistant
              </div>
            </div>
          </div>
        </div>

        <div className="watch-chat-messages">
          {PLACEHOLDER_MESSAGES.map((msg, i) => (
            <div key={i} className={`watch-bubble-row ${msg.role}`}>
              {msg.role === 'assistant' && <div className="watch-bubble-avatar">AI</div>}
              <div className={`watch-bubble ${msg.role}`}>
                {msg.text.split('\n\n').map((para, j) => <p key={j}>{para}</p>)}
              </div>
            </div>
          ))}
          <div className="watch-bubble-row assistant">
            <div className="watch-bubble-avatar">AI</div>
            <div className="watch-bubble assistant typing">
              <span /><span /><span />
            </div>
          </div>
        </div>

        <div className="watch-chat-input-area">
          <div className="watch-chat-notice">Chat powered by AI \u2014 responses are contextual to the video.</div>
          <div className="watch-chat-input-row">
            <input
              className="watch-chat-input"
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              placeholder="Ask about this video\u2026"
              disabled
            />
            <button className="watch-chat-send" disabled>&#8593;</button>
          </div>
        </div>
      </div>
    </div>
  )
}
