import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useTheme } from '../../contexts/ThemeContext'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
import './Navbar.css'

export default function Navbar() {
  const { user, logout } = useAuth()
  const { dark, toggleTheme } = useTheme()
  const [hash, setHash] = useState(window.location.hash || '#/')
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    function onHash() { setHash(window.location.hash || '#/') }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const path = hash.replace(/^#/, '') || '/'
  const isActive = (p) => path === p || path.startsWith(p + '/') ? 'active' : ''

  const publicLinks = [
    { label: 'Home', href: '#/' },
    { label: 'Browse Videos', href: '#/browse' },
    { label: 'Pricing', href: '#/pricing' },
    { label: 'How It Works', href: '#/how-it-works' },
  ]

  const loggedInLinks = [
    { label: 'Home', href: '#/' },
    { label: 'Browse Videos', href: '#/browse' },
    { label: 'Dashboard', href: '#/dashboard' },
    { label: 'History', href: '#/history' },
  ]

  const links = user ? loggedInLinks : publicLinks

  const accountItems = [
    { label: 'Profile', icon: '\u2630', onClick: () => window.location.hash = '#/profile' },
    { label: 'Subscription', icon: '\u2606', onClick: () => window.location.hash = '#/subscription' },
    { label: 'Settings', icon: '\u2699', onClick: () => window.location.hash = '#/settings' },
    { divider: true },
    { label: 'Sign Out', icon: '\u2192', danger: true, onClick: () => { logout(); window.location.hash = '#/' } },
  ]

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <a href="#/" className="navbar-logo">
          <div className="navbar-logo-icon">&#9654;</div>
          <span>VideoSearch</span>
        </a>

        <div className={`navbar-links ${menuOpen ? 'open' : ''}`}>
          {links.map(l => {
            const p = l.href.replace('#', '')
            return (
              <a key={l.href} href={l.href} className={`navbar-link ${isActive(p)}`} onClick={() => setMenuOpen(false)}>
                {l.label}
              </a>
            )
          })}
        </div>

        <div className="navbar-actions">
          <button
            className="navbar-theme-toggle"
            onClick={toggleTheme}
            aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-pressed={dark}
          >
            {/* Sun icon — visible in light mode */}
            <svg className="theme-icon theme-icon-sun" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="4.5" />
              <line className="sun-ray" x1="12" y1="2"     x2="12" y2="6"     />
              <line className="sun-ray" x1="12" y1="18"    x2="12" y2="22"    />
              <line className="sun-ray" x1="2"  y1="12"    x2="6"  y2="12"    />
              <line className="sun-ray" x1="18" y1="12"    x2="22" y2="12"    />
              <line className="sun-ray" x1="4.93"  y1="4.93"  x2="7.76"  y2="7.76"  />
              <line className="sun-ray" x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
              <line className="sun-ray" x1="4.93"  y1="19.07" x2="7.76"  y2="16.24" />
              <line className="sun-ray" x1="16.24" y1="7.76"  x2="19.07" y2="4.93"  />
            </svg>

            {/* Moon icon — visible in dark mode */}
            <svg className="theme-icon theme-icon-moon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          </button>

          {user ? (
            <>
              <a href="#/notifications" className={`navbar-notif ${isActive('/notifications')}`} title="Notifications">
                &#128276;
              </a>
              <Dropdown
                trigger={<Avatar name={user.name && user.surname ? `${user.name} ${user.surname}` : user.username} size="sm" />}
                items={accountItems}
                align="right"
              />
            </>
          ) : (
            <>
              <a href="#/login" className="navbar-login">Log In</a>
              <a href="#/signup" className="navbar-signup">Sign Up</a>
            </>
          )}
          <button className="navbar-hamburger" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? '\u2715' : '\u2630'}
          </button>
        </div>
      </div>
    </nav>
  )
}
