import { useRef, useState } from 'react'
import MarkdownMessage from './components/MarkdownMessage'
import './ExplainPage.css'

function parseYouTubeId(url) {
  const patterns = [
    /(?:v=)([^&\n?#]+)/,
    /(?:youtu\.be\/)([^&\n?#]+)/,
    /(?:embed\/)([^&\n?#]+)/,
  ]
  for (const re of patterns) {
    const match = url.match(re)
    if (match) return match[1]
  }
  return null
}

const DEFAULT_VIDEO_ID = 'aircAruvnKk'

const PLACEHOLDER_MESSAGES = [
  {
    role: 'assistant',
    text: 'Hi! Paste a YouTube link above and I will help you understand the video. You can ask me anything about its content.',
  },
  {
    role: 'user',
    text: 'What is a neural network?',
  },
  {
    role: 'assistant',
    text: 'A neural network is a system of layers of interconnected nodes loosely inspired by the human brain. Each layer transforms its input and passes it forward, and the final layer produces a prediction or output.\n\nIn this video, 3Blue1Brown visualizes how weights and biases shape those transformations.',
  },
]

const API_BASE = 'http://localhost:8000'

export default function ExplainPage() {
  const [urlInput, setUrlInput] = useState('')
  const [videoId, setVideoId] = useState(DEFAULT_VIDEO_ID)
  const [localVideoUrl, setLocalVideoUrl] = useState(null)
  const [urlError, setUrlError] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const fileInputRef = useRef(null)

  function handleLoadVideo() {
    const id = parseYouTubeId(urlInput.trim())
    if (id) {
      setVideoId(id)
      setLocalVideoUrl(null)
      setUrlError(false)
      return
    }

    setUrlError(true)
  }

  function handleUrlKeyDown(event) {
    if (event.key === 'Enter') handleLoadVideo()
  }

  async function handleFileChange(event) {
    const file = event.target.files[0]
    if (!file) return

    setUploading(true)
    setUploadError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_BASE}/files/upload_video`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}))
        throw new Error(errorBody.detail || `Upload failed (${response.status})`)
      }

      const data = await response.json()
      setLocalVideoUrl(`${API_BASE}${data.url}`)
      setVideoId(null)
    } catch (error) {
      setUploadError(error.message)
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  function handleUploadVideo() {
    fileInputRef.current?.click()
  }

  return (
    <div className="explain-layout">
      <div className="explain-left">
        <div className="url-bar">
          <div className="url-input-group">
            <span className="url-icon">▶</span>
            <input
              className={urlError ? 'url-input error' : 'url-input'}
              value={urlInput}
              onChange={event => {
                setUrlInput(event.target.value)
                setUrlError(false)
              }}
              onKeyDown={handleUrlKeyDown}
              placeholder="Paste a YouTube URL and press Enter..."
            />
          </div>

          <div className="url-actions">
            <button className="url-load-btn" onClick={handleLoadVideo}>
              Load
            </button>
            <button className="url-upload-btn" onClick={handleUploadVideo}>
              Upload File
            </button>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="video/*"
            style={{ display: 'none' }}
          />
        </div>

        {urlError && (
          <div className="url-error">Could not parse a YouTube video ID from that URL.</div>
        )}
        {uploadError && (
          <div className="url-error">{uploadError}</div>
        )}
        {uploading && (
          <div className="upload-status">Uploading video...</div>
        )}

        <div className="video-embed-wrapper">
          {localVideoUrl ? (
            <video
              key={localVideoUrl}
              className="video-embed"
              src={localVideoUrl}
              controls
            />
          ) : (
            <iframe
              key={videoId}
              className="video-embed"
              src={`https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1`}
              title="YouTube video"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          )}
        </div>

        <div className="video-details">
          <div className="video-details-title">
            {localVideoUrl
              ? 'Uploaded video'
              : videoId === DEFAULT_VIDEO_ID
                ? 'But what is a neural network? - 3Blue1Brown'
                : 'Video loaded'}
          </div>
          <div className="video-details-meta">
            <span className="placeholder-tag">Placeholder</span>
            <span>Title, description and transcript will be fetched by the backend</span>
          </div>

          <div className="segment-row">
            <div className="segment-label">Segments</div>
            <div className="segment-list">
              {[
                '0:00 Introduction',
                '1:42 Neurons and layers',
                '4:10 Weights and biases',
                '7:30 Activation functions',
                '11:05 Training overview',
              ].map((segment, index) => (
                <button key={segment} className={`segment-chip ${index === 1 ? 'segment-active' : ''}`}>
                  {segment}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="explain-right">
        <div className="chat-header">
          <div className="chat-header-left">
            <div className="chat-avatar">AI</div>
            <div>
              <div className="chat-name">VideoSearch Explainer</div>
              <div className="chat-status">
                <span className="status-dot" />
                LLM API not connected yet
              </div>
            </div>
          </div>
          <span className="placeholder-tag">Placeholder</span>
        </div>

        <div className="chat-messages">
          {PLACEHOLDER_MESSAGES.map((message, index) => (
            <div key={index} className={`chat-bubble-row ${message.role}`}>
              {message.role === 'assistant' && (
                <div className="bubble-avatar">AI</div>
              )}
              <div className={`chat-bubble ${message.role}`}>
                {message.role === 'assistant'
                  ? <MarkdownMessage content={message.text} />
                  : message.text.split('\n\n').map((paragraph, paragraphIndex) => (
                      <p key={paragraphIndex}>{paragraph}</p>
                    ))
                }
              </div>
            </div>
          ))}

          <div className="chat-bubble-row assistant">
            <div className="bubble-avatar">AI</div>
            <div className="chat-bubble assistant typing">
              <span />
              <span />
              <span />
            </div>
          </div>
        </div>

        <div className="chat-input-area">
          <div className="chat-input-notice">
            Chat will be powered by the LLM API soon.
          </div>
          <div className="chat-input-row">
            <input
              className="chat-input"
              value={chatInput}
              onChange={event => setChatInput(event.target.value)}
              placeholder="Ask about this video..."
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
