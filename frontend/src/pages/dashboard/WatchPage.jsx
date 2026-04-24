import { useState, useRef, useEffect } from 'react'
import { ALL_VIDEOS } from '../../data/data'
import { useHistory } from '../../contexts/HistoryContext'
import { useAuth } from '../../contexts/AuthContext'
import { useUserVideos } from '../../contexts/UserVideosContext'
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

const TRANSCRIPTION_WORDS = [
  'Transcribing audio',
  'Processing speech',
  'Analyzing content',
  'Building transcript',
  'Extracting segments',
  'Indexing context',
  'Generating embeddings',
  'Finalizing',
]

const WELCOME_MESSAGE = {
  role: 'assistant',
  text: 'Hi! Paste a YouTube link above and I\'ll help you understand the video. You can ask me anything about its content.',
}

const chatKey = (userId, vid) => `watchChat_${userId || 'anonymous'}_${vid}`
const legacyChatKey = (vid) => `watchChat_${vid}`
const API_BASE = 'http://localhost:8000'
const TRANSCRIPTION_POLL_MS = 2500

function youtubeWatchUrl(videoId) {
  return `https://www.youtube.com/watch?v=${videoId}`
}

function formatElapsed(seconds) {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return s === 0 ? `${m}m` : `${m}m ${s}s`
}

async function loadHistoryFromAPI(videoId) {
  const token = localStorage.getItem('auth_token')
  if (!token || !videoId) return null
  const res = await fetch(`${API_BASE}/chat-history/${videoId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) return null
  const rows = await res.json()
  return rows.map(r => ({ role: r.role, text: r.content }))
}

async function sendMessageToAPI(videoId, messages, frameBase64, currentTimeS) {
  const res = await fetch(`${API_BASE}/chat/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
    },
    body: JSON.stringify({
      video_id: videoId,
      message: messages
        .filter(m => m.role === 'user')
        .map(m => ({ role: m.role, content: m.text })),
      ...(frameBase64 ? { frame_base64: frameBase64 } : {}),
      ...(currentTimeS != null ? { current_time_s: currentTimeS } : {}),
    }),
  })
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  const data = await res.json()
  const msg = data.choices[0].message

  // Return both text content and any tool calls
  return {
    text: msg.content || '',
    toolCalls: msg.tool_calls || [],
  }
}

// Load YouTube IFrame API script once
function loadYouTubeAPI() {
  return new Promise((resolve) => {
    if (window.YT && window.YT.Player) {
      resolve()
      return
    }
    if (!document.getElementById('yt-iframe-api')) {
      const tag = document.createElement('script')
      tag.id = 'yt-iframe-api'
      tag.src = 'https://www.youtube.com/iframe_api'
      document.head.appendChild(tag)
    }
    const prev = window.onYouTubeIframeAPIReady
    window.onYouTubeIframeAPIReady = () => {
      prev?.()
      resolve()
    }
  })
}

export default function WatchPage({ params }) {
  const { recordVisit, recordChat } = useHistory()
  const { user } = useAuth()
  const { addUserVideo } = useUserVideos()
  const videoFromParams = params?.id ? ALL_VIDEOS.find(v => v.id === parseInt(params.id)) : null
  const defaultYoutubeId = videoFromParams?.youtubeId || 'aircAruvnKk'
  const defaultTitle = videoFromParams?.title || 'But what is a neural network? \u2014 3Blue1Brown'

  const [chatWidth, setChatWidth] = useState(400)
  const [chatHeight, setChatHeight] = useState(null)
  const [isMobile, setIsMobile] = useState(() => window.innerWidth <= 900)
  const isResizing = useRef(false)
  const ytPlayerRef = useRef(null)
  const ytReadyRef = useRef(false)
  const ytContainerRef = useRef(null)

  function handleResizerMouseDown() {
    const isMobile = window.innerWidth <= 900
    isResizing.current = true
    document.body.style.cursor = isMobile ? 'row-resize' : 'col-resize'
    document.body.style.userSelect = 'none'

    function onMouseMove(e) {
      if (!isResizing.current) return
      if (isMobile) {
        const layoutEl = e.target.closest?.('.watch-layout') ?? document.querySelector('.watch-layout')
        const layoutRect = layoutEl?.getBoundingClientRect()
        if (!layoutRect) return
        const newHeight = layoutRect.bottom - e.clientY
        setChatHeight(Math.min(window.innerHeight * 0.8, Math.max(120, newHeight)))
      } else {
        const newWidth = window.innerWidth - e.clientX
        setChatWidth(Math.min(700, Math.max(280, newWidth)))
      }
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

  // Read a user video to pre-load (set by Browse/Dashboard when clicking a personal video)
  const [pendingVideo] = useState(() => {
    const raw = sessionStorage.getItem('openUserVideo')
    if (raw) {
      sessionStorage.removeItem('openUserVideo')
      try {
        return JSON.parse(raw)
      } catch {
        return null
      }
    }
    return null
  })

  const SESSION_KEY = 'watchpage_session'

  function loadChat(vid) {
    try {
      return JSON.parse(localStorage.getItem(chatKey(user?.id, vid))) ?? [WELCOME_MESSAGE]
    } catch {
      return [WELCOME_MESSAGE]
    }
  }

  const [urlInput, setUrlInput] = useState(() => {
    if (videoFromParams) return ''
    try { return JSON.parse(localStorage.getItem(SESSION_KEY))?.urlInput ?? '' } catch { return '' }
  })
  const [videoId, setVideoId] = useState(() => {
    if (pendingVideo?.type === 'youtube') return pendingVideo.youtubeId
    if (pendingVideo?.type === 'upload') return ''  // uploads don't use YouTube player
    if (pendingVideo?.type === 'chat_only') return pendingVideo.chatVideoId || ''
    if (videoFromParams) return defaultYoutubeId
    try { return JSON.parse(localStorage.getItem(SESSION_KEY))?.videoId ?? defaultYoutubeId } catch { return defaultYoutubeId }
  })
  // Separate state for uploaded video UUID — used for API calls only, never fed to YouTube player
  const [uploadedVideoId, setUploadedVideoId] = useState(() => {
    if (pendingVideo?.type === 'upload') return pendingVideo.videoId || null
    return null
  })
  const [localVideoUrl, setLocalVideoUrl] = useState(() => {
    if (pendingVideo?.type === 'upload') return pendingVideo.localUrl
    return null
  })
  const [videoTitle, setVideoTitle] = useState(() => {
    if (pendingVideo) return pendingVideo.title
    if (videoFromParams) return defaultTitle
    try { return JSON.parse(localStorage.getItem(SESSION_KEY))?.videoTitle ?? defaultTitle } catch { return defaultTitle }
  })
  const [urlError, setUrlError] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [messages, setMessages] = useState(() => {
    const initialVideoId = pendingVideo?.youtubeId
      || (pendingVideo?.type === 'upload' ? pendingVideo.videoId : null)
      || pendingVideo?.chatVideoId
      || defaultYoutubeId
    return loadChat(initialVideoId)
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [videoLoadError, setVideoLoadError] = useState(false)
  const [ytVideoError, setYtVideoError] = useState(false)
  const [transcriptionStatus, setTranscriptionStatus] = useState('checking')
  const [segments, setSegments] = useState([])
  const [activeSegIdx, setActiveSegIdx] = useState(null)
  const [segmentsVisible, setSegmentsVisible] = useState(true)
  const [transcriptionElapsed, setTranscriptionElapsed] = useState(0)
  const transcriptionTimerRef = useRef(null)
  const transcriptionStartRef = useRef(null)
  const [wordIdx, setWordIdx] = useState(0)
  const [wordFade, setWordFade] = useState(true)
  const [chatCollapsed, setChatCollapsed] = useState(false)
  const [theaterMode, setTheaterMode] = useState(false)
  const [theaterExiting, setTheaterExiting] = useState(false)
  const [frameCaptureArmed, setFrameCaptureArmed] = useState(false)

  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const inputRef = useRef(null)
  const fileInputRef = useRef(null)
  const transcriptionStartedRef = useRef(new Set())

  const activeVideoId = uploadedVideoId || videoId
  const isTranscriptionReady = transcriptionStatus === 'ready'
  const isTranscriptionFailed = transcriptionStatus === 'failed'
  const chatDisabled = isLoading || !isTranscriptionReady
  const transcriptionNotice = (() => {
    if (isTranscriptionReady) return 'Chat powered by AI - responses are contextual to the video.'
    if (isTranscriptionFailed) return 'Transcription failed. Load the video again or try another video.'
    if (transcriptionStatus === 'missing') return 'Preparing transcription before chat becomes available.'
    if (transcriptionStatus === 'chunking') return 'Indexing transcript for contextual answers.'
    if (transcriptionStatus === 'summarizing') return 'Finishing transcript analysis.'
    return 'Transcribing video before chat becomes available.'
  })()

  useEffect(() => {
    if (params?.id) recordVisit(params.id)
  }, [params?.id, recordVisit])

  useEffect(() => {
    function onResize() {
      const mobile = window.innerWidth <= 900
      setIsMobile(mobile)
      if (!mobile) setChatHeight(null)
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  useEffect(() => {
    const vid = uploadedVideoId || videoId
    if (!vid) return
    loadHistoryFromAPI(vid).then(history => {
      if (history !== null) {
        if (history.length) {
          setMessages(history)
        } else {
          setMessages([WELCOME_MESSAGE])
          try {
            localStorage.removeItem(chatKey(user?.id, vid))
            localStorage.removeItem(legacyChatKey(vid))
          } catch {
            // Ignore storage cleanup failures.
          }
        }
      }
    })
  }, [videoId, uploadedVideoId, user?.id])

  useEffect(() => {
    try {
      localStorage.setItem(SESSION_KEY, JSON.stringify({ urlInput, videoId, videoTitle }))
    } catch {
      // Ignore storage write failures.
    }
  }, [videoId, videoTitle, urlInput])

  useEffect(() => {
    const vid = uploadedVideoId || videoId
    if (!vid) return
    try {
      localStorage.setItem(chatKey(user?.id, vid), JSON.stringify(messages))
    } catch {
      // Ignore storage write failures.
    }
  }, [messages, uploadedVideoId, user?.id, videoId])

  useEffect(() => {
    setTranscriptionStatus(activeVideoId ? 'checking' : 'missing')
    setSegments([])
    setActiveSegIdx(null)
    setTranscriptionElapsed(0)
    transcriptionStartRef.current = null
    if (transcriptionTimerRef.current) clearInterval(transcriptionTimerRef.current)
  }, [activeVideoId])

  useEffect(() => {
    const done = transcriptionStatus === 'ready' || transcriptionStatus === 'failed'
    const active = !done && transcriptionStatus !== 'missing'

    if (active) {
      if (!transcriptionStartRef.current) {
        transcriptionStartRef.current = Date.now()
      }
      if (!transcriptionTimerRef.current) {
        transcriptionTimerRef.current = setInterval(() => {
          setTranscriptionElapsed(Math.floor((Date.now() - transcriptionStartRef.current) / 1000))
        }, 1000)
      }
    } else {
      if (transcriptionTimerRef.current) {
        clearInterval(transcriptionTimerRef.current)
        transcriptionTimerRef.current = null
      }
    }

    return () => {
      if (transcriptionTimerRef.current) {
        clearInterval(transcriptionTimerRef.current)
        transcriptionTimerRef.current = null
      }
    }
  }, [transcriptionStatus])

  useEffect(() => {
    if (!videoId || localVideoUrl) return
    const token = localStorage.getItem('auth_token')
    if (!token) return

    const startKey = `youtube:${videoId}`
    if (transcriptionStartedRef.current.has(startKey)) return
    transcriptionStartedRef.current.add(startKey)

    fetch(`${API_BASE}/transcription/url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ url: youtubeWatchUrl(videoId) }),
    }).catch(() => {
      setTranscriptionStatus('failed')
    })
  }, [localVideoUrl, videoId])

  useEffect(() => {
    if (!activeVideoId) return
    const token = localStorage.getItem('auth_token')
    if (!token) {
      setTranscriptionStatus('failed')
      return
    }

    let cancelled = false
    let timeoutId = null

    async function poll() {
      try {
        const res = await fetch(`${API_BASE}/transcription/status/${encodeURIComponent(activeVideoId)}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) throw new Error(`Status failed: ${res.status}`)
        const data = await res.json()
        if (cancelled) return

        setTranscriptionStatus(data.status || 'missing')
        if (!data.ready) {
          timeoutId = window.setTimeout(poll, TRANSCRIPTION_POLL_MS)
        }
      } catch {
        if (!cancelled) {
          setTranscriptionStatus('checking')
          timeoutId = window.setTimeout(poll, TRANSCRIPTION_POLL_MS)
        }
      }
    }

    poll()
    return () => {
      cancelled = true
      if (timeoutId) window.clearTimeout(timeoutId)
    }
  }, [activeVideoId])

  useEffect(() => {
    if (isTranscriptionReady || isTranscriptionFailed) {
      setWordIdx(0)
      setWordFade(true)
      return
    }
    setWordFade(true)
    const interval = setInterval(() => {
      setWordFade(false)
      setTimeout(() => {
        setWordIdx(i => (i + 1) % TRANSCRIPTION_WORDS.length)
        setWordFade(true)
      }, 350)
    }, 2800)
    return () => clearInterval(interval)
  }, [isTranscriptionReady, isTranscriptionFailed])

  useEffect(() => {
    if (transcriptionStatus !== 'ready' || !activeVideoId) return
    const token = localStorage.getItem('auth_token')
    if (!token) return
    fetch(`${API_BASE}/transcription/segments/${encodeURIComponent(activeVideoId)}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.segments?.length) setSegments(data.segments)
      })
      .catch(() => {})
  }, [transcriptionStatus, activeVideoId])

  useEffect(() => {
    const container = messagesContainerRef.current
    if (container) container.scrollTop = container.scrollHeight
  }, [messages, isLoading])

  function exitTheater() {
    setTheaterExiting(true)
    setTimeout(() => {
      setTheaterMode(false)
      setTheaterExiting(false)
    }, 280)
  }

  useEffect(() => {
    if (!theaterMode) return
    function onKeyDown(e) { if (e.key === 'Escape') exitTheater() }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [theaterMode])

  // Initialize YouTube IFrame Player API
  useEffect(() => {
    if (!videoId || localVideoUrl) return
    let cancelled = false
    loadYouTubeAPI().then(() => {
      if (cancelled || !ytContainerRef.current) return
      if (ytPlayerRef.current) {
        try {
          ytPlayerRef.current.destroy()
        } catch {
          // Ignore player cleanup failures.
        }
        ytPlayerRef.current = null
      }
      ytReadyRef.current = false
      setYtVideoError(false)
      // YT.Player replaces the target element with an <iframe>. Give it a
      // disposable child so React keeps ownership of the ref'd wrapper.
      const mount = document.createElement('div')
      ytContainerRef.current.innerHTML = ''
      ytContainerRef.current.appendChild(mount)
      ytPlayerRef.current = new window.YT.Player(mount, {
        videoId,
        width: '100%',
        height: '100%',
        playerVars: { rel: 0, modestbranding: 1 },
        events: {
          onReady: () => { ytReadyRef.current = true },
          onError: () => { if (!cancelled) setYtVideoError(true) },
        },
      })
    })
    return () => {
      cancelled = true
      if (ytPlayerRef.current) {
        try {
          ytPlayerRef.current.destroy()
        } catch {
          // Ignore player cleanup failures.
        }
        ytPlayerRef.current = null
      }
    }
  }, [videoId, localVideoUrl])

  function getLocalVideoEl() {
    return document.querySelector('video.watch-embed')
  }

  function seekTo(seconds) {
    if (localVideoUrl) {
      const el = getLocalVideoEl()
      if (el) { el.currentTime = seconds; el.play() }
    } else if (ytReadyRef.current) {
      ytPlayerRef.current?.seekTo(seconds, true)
      ytPlayerRef.current?.playVideo()
    }
  }

  function executeToolCalls(toolCalls) {
    const yt = ytReadyRef.current ? ytPlayerRef.current : null

    for (const call of toolCalls) {
      const name = call.function?.name
      const args = JSON.parse(call.function?.arguments || '{}')

      if (name === 'play_video') {
        if (localVideoUrl) {
          getLocalVideoEl()?.play()
        } else {
          yt?.playVideo()
        }
      } else if (name === 'pause_video') {
        if (localVideoUrl) {
          getLocalVideoEl()?.pause()
        } else {
          yt?.pauseVideo()
        }
      } else if (name === 'seek_video') {
        const seconds = args.seconds ?? 0
        const currentTime = localVideoUrl
          ? (getLocalVideoEl()?.currentTime ?? null)
          : (ytReadyRef.current ? ytPlayerRef.current?.getCurrentTime() : null)
        if (currentTime != null && Math.abs(currentTime - seconds) < 20) break
        if (localVideoUrl) {
          const el = getLocalVideoEl()
          if (el) el.currentTime = seconds
        } else {
          yt?.seekTo(seconds, true)
        }
      } else if (name === 'mute_video') {
        if (localVideoUrl) {
          const el = getLocalVideoEl()
          if (el) el.muted = true
        } else {
          yt?.mute()
        }
      } else if (name === 'unmute_video') {
        if (localVideoUrl) {
          const el = getLocalVideoEl()
          if (el) el.muted = false
        } else {
          yt?.unMute()
        }
      }
    }
  }

  function handleLoadVideo() {
    const id = parseYouTubeId(urlInput.trim())
    if (id) {
      setTranscriptionStatus('checking')
      setVideoId(id)
      setUploadedVideoId(null)
      setLocalVideoUrl(null)
      setVideoTitle('Video loaded')
      setUrlError(false)
      setUploadError('')
      setYtVideoError(false)
      setMessages([WELCOME_MESSAGE])
      addUserVideo({ id: `yt_${id}`, type: 'youtube', youtubeId: id, title: 'Video loaded', addedAt: new Date().toISOString() })

      // Trigger transcription in the background
      const token = localStorage.getItem('auth_token')
      transcriptionStartedRef.current.add(`youtube:${id}`)
      fetch(`${API_BASE}/transcription/url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ url: urlInput.trim() }),
      }).catch(() => setTranscriptionStatus('failed'))
    } else {
      setUrlError(true)
    }
  }

  function handleUrlKeyDown(e) {
    if (e.key === 'Enter') handleLoadVideo()
  }

  async function handleSendMessage() {
    const text = chatInput.trim()
    if (!text || chatDisabled) return

    const shouldCapture = frameCaptureArmed && videoId && !localVideoUrl
    setFrameCaptureArmed(false)

    const userMessage = { role: 'user', text }
    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setChatInput('')
    if (inputRef.current) inputRef.current.style.height = 'auto'
    setIsLoading(true)
    recordChat(uploadedVideoId || videoId)

    const frameBase64 = shouldCapture ? await captureCurrentFrame() : null

    const currentTimeS = localVideoUrl
      ? (getLocalVideoEl()?.currentTime ?? null)
      : (ytReadyRef.current ? (ytPlayerRef.current?.getCurrentTime() ?? null) : null)

    try {
      const { text, toolCalls } = await sendMessageToAPI(uploadedVideoId || videoId, updatedMessages, frameBase64, currentTimeS)

      // Execute any tool calls (play/pause)
      if (toolCalls.length > 0) {
        executeToolCalls(toolCalls)
      }

      // Show text reply, or a fallback describing the action
      const replyText = text
        || toolCalls.map(tc => `*${tc.function.name.replace('_', ' ')}*`).join(', ')
        || 'Done.'
      setMessages(prev => [...prev, { role: 'assistant', text: replyText }])
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
      const res = await fetch(`${API_BASE}/files/upload_video`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('auth_token')}` },
        body: formData,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Upload failed (${res.status})`)
      }

      const data = await res.json()
      const videoUrl = `${API_BASE}${data.url}`
      setTranscriptionStatus('checking')
      setLocalVideoUrl(videoUrl)
      setVideoId('')
      setUploadedVideoId(data.user_video_id || null)
      setVideoTitle(file.name)
      setMessages([WELCOME_MESSAGE])
      addUserVideo({ id: `upload_${Date.now()}`, type: 'upload', localUrl: videoUrl, title: file.name, addedAt: new Date().toISOString(), videoId: data.user_video_id || null })
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

  async function captureCurrentFrame() {
    if (!ytReadyRef.current || !videoId) return null
    const timestamp = ytPlayerRef.current.getCurrentTime()
    try {
      const res = await fetch(`${API_BASE}/capture-frame`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({ video_id: videoId, timestamp }),
      })
      if (!res.ok) return null
      const data = await res.json()
      return data.image_base64
    } catch {
      return null
    }
  }

  function handleSegmentClick(seg, idx) {
    setActiveSegIdx(idx)
    if (localVideoUrl) {
      const el = getLocalVideoEl()
      if (el) el.currentTime = seg.seconds
    } else if (ytReadyRef.current) {
      ytPlayerRef.current?.seekTo(seg.seconds, true)
    }
  }

  return (
    <div className={`watch-layout${theaterMode ? ' theater' : ''}${theaterExiting ? ' theater-exit' : ''}${theaterMode && chatCollapsed ? ' theater-chat-hidden' : ''}`}>
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

        <div className={`watch-embed-wrapper${segments.length > 0 && segmentsVisible && !chatCollapsed ? ' compact' : ''}${chatCollapsed ? ' chat-hidden' : ''}`}>
          {localVideoUrl ? (
            videoLoadError ? (
              <div className="watch-no-video">
                <div className="watch-no-video-icon">&#128249;</div>
                <p className="watch-no-video-title">Video not available</p>
                <p className="watch-no-video-sub">
                  Uploaded videos are not stored on our servers for security and privacy reasons.
                  Re-upload the file to continue chatting.
                </p>
              </div>
            ) : (
              <video
                key={localVideoUrl}
                className="watch-embed"
                src={localVideoUrl}
                controls
                onError={() => setVideoLoadError(true)}
              />
            )
          ) : ytVideoError ? (
            <div className="watch-no-video">
              <div className="watch-no-video-icon">&#128249;</div>
              <p className="watch-no-video-title">Video not available</p>
              <p className="watch-no-video-sub">
                This video cannot be played (it may have been deleted, made private, or has embedding disabled).
              </p>
            </div>
          ) : (
            <div
              ref={ytContainerRef}
              className="watch-embed"
            />
          )}
          <button
            className="watch-theater-btn"
            onClick={() => theaterMode ? exitTheater() : setTheaterMode(true)}
            title={theaterMode ? 'Exit theater mode (Esc)' : 'Theater mode'}
          >
            {theaterMode ? '✕' : '⛶'}
          </button>
        </div>

      </div>

      <div className="watch-details">
        <div className="watch-title">{videoTitle}</div>
        {segments.length > 0 && (
          <div className="watch-segments">
            <div className="watch-seg-label">
              Segments
              <button
                className="watch-seg-toggle"
                onClick={() => setSegmentsVisible(v => !v)}
                title={segmentsVisible ? 'Hide segments' : 'Show segments'}
              >
                {segmentsVisible ? '▲' : '▼'}
              </button>
            </div>
            {segmentsVisible && (
              <div className="watch-seg-list">
                {segments.map((seg, i) => (
                  <button
                    key={i}
                    className={`watch-seg-chip ${i === activeSegIdx ? 'active' : ''}`}
                    onClick={() => handleSegmentClick(seg, i)}
                  >
                    {seg.time} {seg.title}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {chatCollapsed && (
        <button className="watch-chat-reopen" onClick={() => setChatCollapsed(false)} title="Open chat">
          «
        </button>
      )}
      <div className="watch-resizer" onMouseDown={handleResizerMouseDown} style={{ display: chatCollapsed ? 'none' : '' }} />

      {/* Right panel - chat */}
      <div
        className={`watch-right${chatCollapsed ? ' collapsed' : ''}`}
        style={{
          width: chatCollapsed ? 0 : chatWidth,
          flex: 'none',
          transition: isResizing.current ? 'none' : 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          ...(isMobile && chatHeight ? { height: chatHeight } : {}),
        }}
      >
        <div className={`watch-chat-inner${chatCollapsed ? ' hidden' : ''}`}>
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
          <button
            className="watch-chat-collapse"
            onClick={() => setChatCollapsed(v => !v)}
            title={chatCollapsed ? 'Expand chat' : 'Collapse chat'}
          >
            {chatCollapsed ? '«' : '»'}
          </button>
        </div>

        <div className="watch-chat-messages" ref={messagesContainerRef}>
          {messages.map((msg, i) => (
            <div key={i} className={`watch-bubble-row ${msg.role}`}>
              {msg.role === 'assistant' && <div className="watch-bubble-avatar">AI</div>}
              <div className={`watch-bubble ${msg.role}`}>
                {msg.role === 'assistant'
                  ? <MarkdownMessage content={msg.text} onTimestampClick={seekTo} />
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
          {!isTranscriptionReady && !isLoading && (
            <div className="watch-bubble-row assistant">
              <div className="watch-bubble-avatar">AI</div>
              <div className="watch-bubble assistant watch-transcription-loading">
                <div className="watch-transcription-spinner" />
                <div className="watch-transcription-info">
                  <span className={`watch-transcription-word ${wordFade ? 'visible' : ''}`}>
                    {TRANSCRIPTION_WORDS[wordIdx]}…
                  </span>
                  <span className="watch-transcription-detail">{transcriptionNotice}</span>
                  {transcriptionElapsed > 0 && (
                    <span className="watch-transcription-timer">{formatElapsed(transcriptionElapsed)}</span>
                  )}
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="watch-chat-input-area">
          <div className="watch-chat-notice">{transcriptionNotice}</div>
          <div className="watch-chat-input-row">
            {videoId && !localVideoUrl && (
              <button
                className={`watch-capture-toggle${frameCaptureArmed ? ' armed' : ''}`}
                onClick={() => setFrameCaptureArmed(v => !v)}
                title={frameCaptureArmed ? 'Frame capture armed — will capture on send' : 'Capture current frame with your next message'}
                disabled={!isTranscriptionReady}
              >
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                  <circle cx="12" cy="13" r="4"/>
                </svg>
              </button>
            )}
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
              placeholder={
                frameCaptureArmed
                  ? 'Ask about the current frame...'
                  : isTranscriptionReady ? 'Ask about this video...' : 'Waiting for transcription...'
              }
              rows={1}
              disabled={!isTranscriptionReady}
            />
            <button
              className="watch-chat-send"
              onClick={handleSendMessage}
              disabled={!chatInput.trim() || chatDisabled}
            >&#8593;</button>
          </div>
        </div>
        </div>
      </div>
    </div>
  )
}
