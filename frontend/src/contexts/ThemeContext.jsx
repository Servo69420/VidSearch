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

  const toggleTheme = useCallback(() => {
    if (busy.current) return
    busy.current = true

    const nextDark = !dark

    if (prefersReducedMotion()) {
      setDark(nextDark)
      busy.current = false
      return
    }

    // Fade veil over the page, swap theme, then fade out
    const veil = document.createElement('div')
    veil.setAttribute('aria-hidden', 'true')
    veil.style.cssText = [
      'position:fixed',
      'inset:0',
      'z-index:9999',
      'pointer-events:none',
      'background:#000',
      'opacity:0',
      'transition:opacity 400ms ease-in-out',
      'will-change:opacity',
    ].join(';')
    document.body.appendChild(veil)

    requestAnimationFrame(() => requestAnimationFrame(() => {
      veil.style.opacity = '0.25'
    }))

    const t1 = setTimeout(() => {
      setDark(nextDark)
      veil.style.opacity = '0'
      const t2 = setTimeout(() => {
        veil.remove()
        busy.current = false
      }, 420)
      timers.current = [t2]
    }, 420)

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
