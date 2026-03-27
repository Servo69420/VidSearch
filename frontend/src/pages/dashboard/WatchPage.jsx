import { useState, useRef, useEffect } from 'react'
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

const WELCOME_MESSAGE = {
  role: 'assistant',
  text: 'Hi! Paste a YouTube link above and I\'ll help you understand the video. You can ask me anything about its content.',
}

async function sendMessageToAPI(videoId, messages) {
  const res = await fetch('http://localhost:8000/chat/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_id: videoId,
      message: messages
        .filter(m => m.role === 'user')
        .map(m => ({ role: m.role, content: m.text })),
    }),
  })
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  const data = await res.json()
  return data.choices[0].message.content
}

export default function WatchPage({ params }) {
  const videoFromParams = params?.id ? ALL_VIDEOS.find(v => v.id === parseInt(params.id)) : null
  const defaultYoutubeId = videoFromParams?.youtubeId || 'aircAruvnKk'
  const defaultTitle = videoFromParams?.title || 'But what is a neural network? \u2014 3Blue1Brown'

  const [urlInput, setUrlInput] = useState('')
  const [videoId, setVideoId] = useState(defaultYoutubeId)
  const [localVideoUrl, setLocalVideoUrl] = useState(null)
  const [videoTitle, setVideoTitle] = useState(defaultTitle)
  const [urlError, setUrlError] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [messages, setMessages] = useState([WELCOME_MESSAGE])
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')

  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  function handleLoadVideo() {
    const id = parseYouTubeId(urlInput.trim())
    if (id) {
      setVideoId(id)
      setLocalVideoUrl(null)
      setVideoTitle('Video loaded')
      setUrlError(false)
      setUploadError('')
      setMessages([WELCOME_MESSAGE])
    } else {
      setUrlError(true)
    }
  }

  function handleUrlKeyDown(e) {
    if (e.key === 'Enter') handleLoadVideo()
  }

  async function handleSendMessage() {
    const text = chatInput.trim()
    if (!text || isLoading) return

    const userMessage = { role: 'user', text }
    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setChatInput('')
    setIsLoading(true)

    try {
      const reply = await sendMessageToAPI(videoId, updatedMessages)
      setMessages(prev => [...prev, { role: 'assistant', text: reply }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Sorry, something went wrong. Please try again.' }])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleChatKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  async function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setUploadError('')
    setUrlError(false)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('http://localhost:8000/files/upload_video', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Upload failed (${res.status})`)
      }

      const data = await res.json()
      setLocalVideoUrl(`http://localhost:8000${data.url}`)
      setVideoId('')
      setVideoTitle(file.name)
      setMessages([WELCOME_MESSAGE])
    } catch (err) {
      setUploadError(err.message || 'Upload failed.')
    } finally {
      setIsUploading(false)
      e.target.value = ''
    }
  }

  function handleUploadClick() {
    fileInputRef.current?.click()
  }

  return (
    <div className="watch-layout">
      {/* Left panel - video */}
      <div className="watch-left">
        <div className="watch-url-bar">
          <div className="watch-url-input-group">
            <span className="watch-url-icon">&#9654;</span>
            <input
              className={`watch-url-input ${urlError ? 'error' : ''}`}
              value={urlInput}
              onChange={e => { setUrlInput(e.target.value); setUrlError(false) }}
              onKeyDown={handleUrlKeyDown}
              placeholder="Paste a YouTube URL and press Enter\u2026"
            />
          </div>
          <div className="watch-url-actions">
            <button className="watch-url-btn" onClick={handleLoadVideo}>Load</button>
            <button className="watch-url-upload-btn" onClick={handleUploadClick}>Upload File</button>
          </div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="video/*"
            style={{ display: 'none' }}
          />
        </div>
        {urlError && <div className="watch-url-error">Could not parse a YouTube video ID from that URL.</div>}
        {uploadError && <div className="watch-url-error">{uploadError}</div>}
        {isUploading && <div className="watch-upload-status">Uploading video...</div>}

        <div className="watch-embed-wrapper">
          {localVideoUrl ? (
            <video
              key={localVideoUrl}
              className="watch-embed"
              src={localVideoUrl}
              controls
            />
          ) : (
            <iframe
              key={videoId}
              className="watch-embed"
              src={`https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1`}
              title="YouTube video"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          )}
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
          {messages.map((msg, i) => (
            <div key={i} className={`watch-bubble-row ${msg.role}`}>
              {msg.role === 'assistant' && <div className="watch-bubble-avatar">AI</div>}
              <div className={`watch-bubble ${msg.role}`}>
                {msg.text.split('\n\n').map((para, j) => <p key={j}>{para}</p>)}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="watch-bubble-row assistant">
              <div className="watch-bubble-avatar">AI</div>
              <div className="watch-bubble assistant typing">
                <span /><span /><span />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="watch-chat-input-area">
          <div className="watch-chat-notice">Chat powered by AI — responses are contextual to the video.</div>
          <div className="watch-chat-input-row">
            <input
              ref={inputRef}
              className="watch-chat-input"
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={handleChatKeyDown}
              placeholder="Ask about this video…"
            />
            <button
              className="watch-chat-send"
              onClick={handleSendMessage}
              disabled={!chatInput.trim() || isLoading}
            >&#8593;</button>          </div>
        </div>
      </div>
    </div>
  )
}
