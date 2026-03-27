import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'

const ThemeContext = createContext()

function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function ThemeProvider({ children }) {
  const [dark, setDark] = useState(() => {
    try { return localStorage.getItem('theme') === 'dark' } catch { return false }
  })

  const busy = useRef(false)
  const timers = useRef([])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
    try { localStorage.setItem('theme', dark ? 'dark' : 'light') } catch {}
  }, [dark])

  useEffect(() => () => timers.current.forEach(clearTimeout), [])

  const toggleTheme = useCallback((e) => {
    if (busy.current) return
    busy.current = true

    const nextDark = !dark

    // ── Reduced-motion: instant swap ─────────────────────────────
    if (prefersReducedMotion()) {
      setDark(nextDark)
      busy.current = false
      return
    }

    // ── Origin: button center, falls back to top-center ──────────
    const rect = e?.currentTarget?.getBoundingClientRect?.()
    const ox = rect ? Math.round(rect.left + rect.width / 2) : window.innerWidth / 2
    const oy = rect ? Math.round(rect.top + rect.height / 2) : 32

    // Radius large enough to cover every viewport corner
    const maxR = Math.ceil(Math.max(
      Math.hypot(ox, oy),
      Math.hypot(window.innerWidth - ox, oy),
      Math.hypot(ox, window.innerHeight - oy),
      Math.hypot(window.innerWidth - ox, window.innerHeight - oy),
    )) + 4

    // Veil = leaving theme's background, covering full viewport
    const oldBg = dark ? '#0f172a' : '#F8FAFC'
    const veil = document.createElement('div')
    veil.setAttribute('aria-hidden', 'true')
    veil.style.cssText = [
      'position:fixed',
      'inset:0',
      'z-index:9999',
      'pointer-events:none',
      `background:${oldBg}`,
      `clip-path:circle(${maxR}px at ${ox}px ${oy}px)`,
      'will-change:clip-path',
    ].join(';')
    document.body.appendChild(veil)

    // Switch theme now — new theme applies beneath the veil
    setDark(nextDark)

    // After paint: collapse the circle back into the toggle origin
    requestAnimationFrame(() => requestAnimationFrame(() => {
      veil.style.transition = 'clip-path 500ms cubic-bezier(0.0, 0.0, 0.2, 1.0)'
      veil.style.clipPath = `circle(0px at ${ox}px ${oy}px)`
    }))

    // Cleanup
    const t1 = setTimeout(() => {
      veil.remove()
      busy.current = false
    }, 540)

    timers.current = [t1]
  }, [dark])

  return (
    <ThemeContext.Provider value={{ dark, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}
