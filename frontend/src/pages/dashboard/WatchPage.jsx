import { useState, useRef, useEffect } from 'react'
import { ALL_VIDEOS } from '../../data/data'
import { useHistory } from '../../contexts/HistoryContext'
import MarkdownMessage from '../../components/MarkdownMessage'
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
  const { recordVisit, recordChat } = useHistory()
  const videoFromParams = params?.id ? ALL_VIDEOS.find(v => v.id === parseInt(params.id)) : null
  const defaultYoutubeId = videoFromParams?.youtubeId || 'aircAruvnKk'
  const defaultTitle = videoFromParams?.title || 'But what is a neural network? \u2014 3Blue1Brown'

  const [chatWidth, setChatWidth] = useState(400)
  const isResizing = useRef(false)

  function handleResizerMouseDown(e) {
    isResizing.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    function onMouseMove(e) {
      if (!isResizing.current) return
      const newWidth = window.innerWidth - e.clientX
      setChatWidth(Math.min(700, Math.max(280, newWidth)))
    }

    function onMouseUp() {
      isResizing.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
    }

    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
  }

  const SESSION_KEY = 'watchpage_session'
  const chatKey = (vid) => `watchChat_${vid}`

  function loadChat(vid) {
    try { return JSON.parse(localStorage.getItem(chatKey(vid))) ?? [WELCOME_MESSAGE] } catch { return [WELCOME_MESSAGE] }
  }

  const [urlInput, setUrlInput] = useState(() => {
    if (videoFromParams) return ''
    try { return JSON.parse(localStorage.getItem(SESSION_KEY))?.urlInput ?? '' } catch { return '' }
  })
  const [videoId, setVideoId] = useState(() => {
    if (videoFromParams) return defaultYoutubeId
    try { return JSON.parse(localStorage.getItem(SESSION_KEY))?.videoId ?? defaultYoutubeId } catch { return defaultYoutubeId }
  })
  const [localVideoUrl, setLocalVideoUrl] = useState(null)
  const [videoTitle, setVideoTitle] = useState(() => {
    if (videoFromParams) return defaultTitle
    try { return JSON.parse(localStorage.getItem(SESSION_KEY))?.videoTitle ?? defaultTitle } catch { return defaultTitle }
  })
  const [urlError, setUrlError] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [messages, setMessages] = useState(() => {
    return loadChat(defaultYoutubeId)
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')

  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const inputRef = useRef(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    if (params?.id) recordVisit(params.id)
  }, [params?.id])

  useEffect(() => {
    try { localStorage.setItem(SESSION_KEY, JSON.stringify({ urlInput, videoId, videoTitle })) } catch {}
  }, [videoId, videoTitle, urlInput])

  useEffect(() => {
    if (!videoId) return
    try { localStorage.setItem(chatKey(videoId), JSON.stringify(messages)) } catch {}
  }, [messages, videoId])

  useEffect(() => {
    const container = messagesContainerRef.current
    if (container) container.scrollTop = container.scrollHeight
  }, [messages, isLoading])

  function handleLoadVideo() {
    const id = parseYouTubeId(urlInput.trim())
    if (id) {
      setVideoId(id)
      setLocalVideoUrl(null)
      setVideoTitle('Video loaded')
      setUrlError(false)
      setUploadError('')
      setMessages(loadChat(id))
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
    recordChat(videoId)

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

      <div className="watch-resizer" onMouseDown={handleResizerMouseDown} />

      {/* Right panel - chat */}
      <div className="watch-right" style={{ width: chatWidth, flex: 'none' }}>
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

        <div className="watch-chat-messages" ref={messagesContainerRef}>
          {messages.map((msg, i) => (
            <div key={i} className={`watch-bubble-row ${msg.role}`}>
              {msg.role === 'assistant' && <div className="watch-bubble-avatar">AI</div>}
              <div className={`watch-bubble ${msg.role}`}>
                {msg.role === 'assistant'
                  ? <MarkdownMessage content={msg.text} />
                  : msg.text.split('\n\n').map((para, j) => <p key={j}>{para}</p>)
                }
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
            <textarea
              ref={inputRef}
              className="watch-chat-input"
              value={chatInput}
              onChange={e => {
                setChatInput(e.target.value)
                e.target.style.height = 'auto'
                e.target.style.height = e.target.scrollHeight + 'px'
              }}
              onKeyDown={handleChatKeyDown}
              placeholder="Ask about this video…"
              rows={1}
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
